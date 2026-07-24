from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from application.ai.reader_provider import LocalReaderAiProvider, get_reader_ai_provider, set_reader_ai_provider


def _config(**overrides: object) -> SimpleNamespace:
    values = {
        "reader_ai_provider": "local",
        "reader_ai_openai_api_key": "",
        "reader_ai_openai_base_url": "https://api.example/v1",
        "reader_ai_openai_chat_model": "gpt-test",
        "reader_ai_openai_image_model": "image-test",
        "reader_ai_openai_speech_model": "tts-test",
        "reader_ai_openai_speech_voice": "alloy",
        "reader_ai_openai_image_size": "1024x1024",
        "reader_ai_voice_provider": "",
        "reader_ai_google_tts_language_code": "en-US",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _bootstrap_function() -> object:
    try:
        from infrastructure.ai.provider_bootstrap import configure_reader_ai_provider
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing reader provider bootstrap: {exc}")
    return configure_reader_ai_provider


@pytest.mark.asyncio
async def test_bootstrap_registers_openai_provider_only_when_explicitly_configured(
    tmp_path: Path,
) -> None:
    set_reader_ai_provider(None)

    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200))) as client:
        provider = _bootstrap_function()(
            config=_config(
                reader_ai_provider="openai",
                reader_ai_openai_api_key="test-key",
            ),
            http_client=client,
            voice_output_dir=tmp_path,
        )

    assert provider.__class__.__name__ == "OpenAICompatibleReaderAiProvider"
    assert get_reader_ai_provider() is provider


@pytest.mark.asyncio
async def test_bootstrap_registers_deepseek_as_openai_compatible_provider(
    tmp_path: Path,
) -> None:
    set_reader_ai_provider(None)

    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200))) as client:
        provider = _bootstrap_function()(
            config=_config(
                reader_ai_provider="deepseek",
                reader_ai_openai_api_key="test-key",
                reader_ai_openai_base_url="",
                reader_ai_openai_chat_model="",
            ),
            http_client=client,
            voice_output_dir=tmp_path,
        )

    assert provider.__class__.__name__ == "OpenAICompatibleReaderAiProvider"
    assert provider.provider_name == "deepseek"
    assert provider.base_url == "https://api.deepseek.com"
    assert provider.chat_model == "deepseek-v4-flash"
    assert get_reader_ai_provider() is provider


@pytest.mark.asyncio
async def test_bootstrap_wraps_voice_with_google_tts_provider(tmp_path: Path) -> None:
    set_reader_ai_provider(None)

    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200))) as client:
        provider = _bootstrap_function()(
            config=_config(
                reader_ai_provider="deepseek",
                reader_ai_openai_api_key="test-key",
                reader_ai_voice_provider="google",
            ),
            http_client=client,
            voice_output_dir=tmp_path,
        )

    assert provider.__class__.__name__ == "GoogleTextToSpeechReaderAiProvider"
    assert provider.provider_name == "google"
    assert provider.fallback.provider_name == "deepseek"
    assert get_reader_ai_provider() is provider


def test_bootstrap_uses_local_provider_when_not_explicitly_openai() -> None:
    set_reader_ai_provider(None)

    provider = _bootstrap_function()(
        config=_config(
            reader_ai_provider="local",
            reader_ai_openai_api_key="test-key",
        )
    )

    assert isinstance(provider, LocalReaderAiProvider)
    assert get_reader_ai_provider() is provider


def test_bootstrap_uses_local_provider_when_openai_key_is_missing() -> None:
    set_reader_ai_provider(None)

    provider = _bootstrap_function()(
        config=_config(
            reader_ai_provider="openai",
            reader_ai_openai_api_key="",
        )
    )

    assert isinstance(provider, LocalReaderAiProvider)
    assert get_reader_ai_provider() is provider
