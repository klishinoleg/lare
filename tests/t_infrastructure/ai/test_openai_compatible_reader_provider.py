from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from application.ai.reader_provider import (
    LocalReaderAiProvider,
    ReaderImageRequest,
    ReaderTextRequest,
    ReaderVoiceRequest,
    ReaderWordExplanationRequest,
)


def _provider_class() -> type:
    try:
        from infrastructure.ai.openai_compatible_reader_provider import (
            OpenAICompatibleReaderAiProvider,
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing OpenAI-compatible reader provider: {exc}")
    return OpenAICompatibleReaderAiProvider


@pytest.mark.asyncio
async def test_openai_provider_translates_text_via_chat_completions() -> None:
    seen_requests: list[dict[str, Any]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        seen_requests.append(
            {
                "path": request.url.path,
                "authorization": request.headers.get("authorization"),
                "payload": payload,
            }
        )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "привет мир"}}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = _provider_class()(
            api_key="test-key",
            base_url="https://api.example/v1",
            chat_model="gpt-test",
            image_model="image-test",
            speech_model="tts-test",
            speech_voice="alloy",
            fallback=LocalReaderAiProvider(),
            http_client=client,
        )

        response = await provider.translate_text(
            ReaderTextRequest(
                account_id=1,
                text="hello world",
                source_language_code="fr",
                target_language_code="ru",
                purpose="translate",
            )
        )

    assert response.content == "привет мир"
    assert response.provider == "openai"
    assert len(seen_requests) == 1
    request = seen_requests[0]
    assert request["path"] == "/v1/chat/completions"
    assert request["authorization"] == "Bearer test-key"
    assert request["payload"]["model"] == "gpt-test"
    serialized_payload = json.dumps(request["payload"], ensure_ascii=False)
    assert "hello world" in serialized_payload
    assert "fr" in serialized_payload
    assert "ru" in serialized_payload
    assert "Original/source language: fr" in serialized_payload


@pytest.mark.asyncio
async def test_openai_provider_builds_word_analysis_prompt_with_source_language() -> None:
    seen_payloads: list[dict[str, Any]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        seen_payloads.append(payload)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "text": "Nous habitons",
                                    "table": [
                                        {
                                            "word": "Nous",
                                            "translate": "мы",
                                            "translit": "ну",
                                            "type": "PRN",
                                            "gender": "",
                                        }
                                    ],
                                }
                            )
                        }
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = _provider_class()(
            api_key="test-key",
            base_url="https://api.example/v1",
            chat_model="deepseek-test",
            image_model="image-test",
            speech_model="tts-test",
            speech_voice="alloy",
            fallback=LocalReaderAiProvider(),
            http_client=client,
            provider_name="deepseek",
        )

        response = await provider.translate_text(
            ReaderTextRequest(
                account_id=1,
                text="Nous habitons",
                source_language_code="fr",
                target_language_code="ru",
                purpose="words",
            )
        )

    assert response.provider == "deepseek"
    assert seen_payloads[0]["response_format"] == {"type": "json_object"}
    serialized_payload = json.dumps(seen_payloads[0], ensure_ascii=False)
    assert "Original/source language: fr" in serialized_payload
    assert "Target language for translations and explanations: ru" in serialized_payload
    assert "Do not include a full-sentence translation" in serialized_payload
    assert "`word`, `translate`, `translit`, `type`, `gender`" in serialized_payload
    assert "row.word must be `du`, not `de` and `le`" in serialized_payload
    assert "row.word must be `habitons`, not `habitions`" in serialized_payload
    assert "IPA pronunciation only" in serialized_payload


@pytest.mark.asyncio
async def test_openai_provider_returns_local_fallback_without_api_key() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("network must not be called without an API key")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = _provider_class()(
            api_key="",
            base_url="https://api.example/v1",
            chat_model="gpt-test",
            image_model="image-test",
            speech_model="tts-test",
            speech_voice="alloy",
            fallback=LocalReaderAiProvider(),
            http_client=client,
        )

        response = await provider.translate_text(
            ReaderTextRequest(account_id=1, text="hello world", target_language_code="ru")
        )

    assert response.content == "hello world [ru]"
    assert response.provider == "local"


@pytest.mark.asyncio
async def test_openai_provider_generates_image_data_url() -> None:
    seen_payloads: list[dict[str, Any]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        seen_payloads.append(payload)
        return httpx.Response(200, json={"data": [{"b64_json": "ZmFrZS1pbWFnZQ=="}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = _provider_class()(
            api_key="test-key",
            base_url="https://api.example/v1",
            chat_model="gpt-test",
            image_model="image-test",
            speech_model="tts-test",
            speech_voice="alloy",
            fallback=LocalReaderAiProvider(),
            http_client=client,
        )

        response = await provider.generate_image(
            ReaderImageRequest(
                account_id=1,
                name="Lazy Story",
                description="A moonlit reading scene",
                fallback_source="data:image/png;base64,fallback",
            )
        )

    assert response.content == "data:image/png;base64,ZmFrZS1pbWFnZQ=="
    assert response.provider == "openai"
    assert seen_payloads[0]["model"] == "image-test"
    assert "Lazy Story" in seen_payloads[0]["prompt"]
    assert "A moonlit reading scene" in seen_payloads[0]["prompt"]
    assert seen_payloads[0]["response_format"] == "b64_json"


@pytest.mark.asyncio
async def test_openai_provider_writes_voice_file_from_speech_response(tmp_path: Path) -> None:
    seen_payloads: list[dict[str, Any]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        seen_payloads.append(payload)
        return httpx.Response(200, content=b"voice-bytes")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = _provider_class()(
            api_key="test-key",
            base_url="https://api.example/v1",
            chat_model="gpt-test",
            image_model="image-test",
            speech_model="tts-test",
            speech_voice="onyx",
            fallback=LocalReaderAiProvider(),
            http_client=client,
            voice_output_dir=tmp_path,
            voice_public_prefix="uploads/ai_voice",
        )

        response = await provider.create_voice(
            ReaderVoiceRequest(
                account_id=1,
                entity="word",
                item_id=7,
                text="hello",
                fallback_file_path="uploads/compat_voice/word_7.wav",
            )
        )

    assert response.content == "uploads/ai_voice/word_7.mp3"
    assert response.file_path == "uploads/ai_voice/word_7.mp3"
    assert response.provider == "openai"
    assert (tmp_path / "word_7.mp3").read_bytes() == b"voice-bytes"
    assert seen_payloads == [
        {
            "model": "tts-test",
            "voice": "onyx",
            "input": "hello",
            "response_format": "mp3",
        }
    ]


@pytest.mark.asyncio
async def test_openai_provider_uses_configured_provider_name_for_word_explanation() -> None:
    seen_payloads: list[dict[str, Any]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_payloads.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "description": "to read or study text",
                                    "root_name": "read",
                                    "root_description": "base reading form",
                                    "parts": [],
                                }
                            )
                        }
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = _provider_class()(
            api_key="test-key",
            base_url="https://api.example",
            chat_model="deepseek-test",
            image_model="image-test",
            speech_model="tts-test",
            speech_voice="alloy",
            fallback=LocalReaderAiProvider(),
            http_client=client,
            provider_name="deepseek",
        )

        response = await provider.explain_word(
            ReaderWordExplanationRequest(
                account_id=1,
                word_id=3,
                word="lecteur",
                source_language_code="fr",
                target_language_code="ru",
            )
        )

    assert response.provider == "deepseek"
    assert response.root_name == "read"
    serialized_payload = json.dumps(seen_payloads[0], ensure_ascii=False)
    assert "Original/source language of the word: fr" in serialized_payload
    assert "Target language for translation, explanation, and descriptions: ru" in serialized_payload
