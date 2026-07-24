from __future__ import annotations

from pathlib import Path

import pytest

from application.ai.reader_provider import (
    LocalReaderAiProvider,
    ReaderTextRequest,
    ReaderVoiceRequest,
)


def _provider_class() -> type:
    try:
        from infrastructure.ai.google_text_to_speech_reader_provider import (
            GoogleTextToSpeechReaderAiProvider,
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing Google text-to-speech reader provider: {exc}")
    return GoogleTextToSpeechReaderAiProvider


@pytest.mark.asyncio
async def test_google_tts_provider_writes_mp3_and_reports_google_provider(tmp_path: Path) -> None:
    seen: list[tuple[str, str]] = []

    async def synthesize(text: str, language_code: str) -> bytes | None:
        seen.append((text, language_code))
        return b"mp3-bytes"

    provider = _provider_class()(
        fallback=LocalReaderAiProvider(),
        synthesize=synthesize,
        language_code="en-US",
        voice_output_dir=tmp_path,
        voice_public_prefix="uploads/ai_voice",
    )

    response = await provider.create_voice(
        ReaderVoiceRequest(
            account_id=1,
            entity="word",
            item_id=7,
            text='Hello "reader"',
            fallback_file_path="uploads/compat_voice/word_7.wav",
        )
    )

    assert response.provider == "google"
    assert response.content == "uploads/ai_voice/word_7.mp3"
    assert response.file_path == "uploads/ai_voice/word_7.mp3"
    assert (tmp_path / "word_7.mp3").read_bytes() == b"mp3-bytes"
    assert seen == [('Hello "reader"', "en-US")]


@pytest.mark.asyncio
async def test_google_tts_provider_uses_request_language_for_voice(tmp_path: Path) -> None:
    seen: list[tuple[str, str]] = []

    async def synthesize(text: str, language_code: str) -> bytes | None:
        seen.append((text, language_code))
        return b"mp3-bytes"

    provider = _provider_class()(
        fallback=LocalReaderAiProvider(),
        synthesize=synthesize,
        language_code="en-US",
        voice_output_dir=tmp_path,
        voice_public_prefix="uploads/ai_voice",
    )

    response = await provider.create_voice(
        ReaderVoiceRequest(
            account_id=1,
            entity="text_part",
            item_id=11,
            text="Nous habitons maintenant a Toulouse.",
            fallback_file_path="uploads/compat_voice/text_part_11.wav",
            language_code="fr",
        )
    )

    assert response.provider == "google"
    assert seen == [("Nous habitons maintenant a Toulouse.", "fr-FR")]


@pytest.mark.asyncio
async def test_google_tts_provider_falls_back_when_synthesis_returns_empty(tmp_path: Path) -> None:
    async def synthesize(text: str, language_code: str) -> bytes | None:
        return None

    provider = _provider_class()(
        fallback=LocalReaderAiProvider(),
        synthesize=synthesize,
        language_code="en-US",
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

    assert response.provider == "local"
    assert response.file_path == "uploads/compat_voice/word_7.wav"
    assert not (tmp_path / "word_7.mp3").exists()
    assert provider.last_voice_error == "empty_google_tts_response"


@pytest.mark.asyncio
async def test_google_tts_provider_records_synthesis_error(tmp_path: Path) -> None:
    async def synthesize(text: str, language_code: str) -> bytes | None:
        raise RuntimeError("google credentials are not ready")

    provider = _provider_class()(
        fallback=LocalReaderAiProvider(),
        synthesize=synthesize,
        language_code="en-US",
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

    assert response.provider == "local"
    assert response.file_path == "uploads/compat_voice/word_7.wav"
    assert provider.last_voice_error
    assert provider.last_voice_error.startswith("RuntimeError:")


@pytest.mark.asyncio
async def test_google_tts_provider_delegates_non_voice_methods() -> None:
    provider = _provider_class()(
        fallback=LocalReaderAiProvider(),
        synthesize=lambda text, language_code: None,
        language_code="en-US",
    )

    response = await provider.translate_text(
        ReaderTextRequest(account_id=1, text="hello", target_language_code="ru")
    )

    assert response.provider == "local"
    assert response.content == "hello [ru]"
