from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from pathlib import Path

from application.ai.reader_provider import (
    ReaderAiProvider,
    ReaderAiProviderResponse,
    ReaderDialogRequest,
    ReaderImageRequest,
    ReaderSegmentRequest,
    ReaderTextRequest,
    ReaderVoiceRequest,
    ReaderWordExplanationRequest,
    ReaderWordExplanationResponse,
)
from core.config import settings


GoogleSpeechSynthesizer = Callable[[str, str], Awaitable[bytes | None] | bytes | None]
logger = logging.getLogger(__name__)


class GoogleTextToSpeechReaderAiProvider:
    provider_name = "google"

    def __init__(
        self,
        *,
        fallback: ReaderAiProvider,
        language_code: str,
        gender: str = "MALE",
        synthesize: GoogleSpeechSynthesizer | None = None,
        voice_output_dir: Path | None = None,
        voice_public_prefix: str | None = None,
    ) -> None:
        self.fallback = fallback
        self.language_code = language_code
        self.gender = gender
        self.synthesize = synthesize or self._synthesize_with_google_cloud
        self.voice_output_dir = voice_output_dir or settings.get_upload_dir() / "ai_voice"
        upload_url = settings.images_upload_url or "uploads"
        self.voice_public_prefix = (voice_public_prefix or f"{upload_url}/ai_voice").strip("/")
        self.last_voice_error: str | None = None

    async def process_segment(self, request: ReaderSegmentRequest) -> ReaderAiProviderResponse:
        return await self.fallback.process_segment(request)

    async def translate_text(self, request: ReaderTextRequest) -> ReaderAiProviderResponse:
        return await self.fallback.translate_text(request)

    async def create_voice(self, request: ReaderVoiceRequest) -> ReaderAiProviderResponse:
        language_code = _normalise_language_code(request.language_code or self.language_code)
        self.last_voice_error = None
        try:
            content = self.synthesize(request.text, language_code)
            if isinstance(content, Awaitable):
                content = await content
        except Exception as exc:  # noqa: BLE001
            self.last_voice_error = f"{exc.__class__.__name__}: {exc}"
            logger.warning("Google TTS synthesis failed: %s", self.last_voice_error)
            content = None

        if not content:
            if self.last_voice_error is None:
                self.last_voice_error = "empty_google_tts_response"
                logger.warning("Google TTS synthesis returned no audio content")
            return await self.fallback.create_voice(request)

        self.voice_output_dir.mkdir(parents=True, exist_ok=True)
        file_name = _voice_file_name(request)
        file_path = self.voice_output_dir / file_name
        file_path.write_bytes(content)
        public_path = f"{self.voice_public_prefix}/{file_name}"
        return ReaderAiProviderResponse(
            content=public_path,
            provider=self.provider_name,
            file_path=public_path,
        )

    async def generate_image(self, request: ReaderImageRequest) -> ReaderAiProviderResponse:
        return await self.fallback.generate_image(request)

    async def answer_dialog(self, request: ReaderDialogRequest) -> ReaderAiProviderResponse:
        return await self.fallback.answer_dialog(request)

    async def explain_word(
        self,
        request: ReaderWordExplanationRequest,
    ) -> ReaderWordExplanationResponse:
        return await self.fallback.explain_word(request)

    async def _synthesize_with_google_cloud(self, text: str, language_code: str) -> bytes | None:
        def _sync_synthesize() -> bytes | None:
            from google.cloud import texttospeech

            client = texttospeech.TextToSpeechClient()
            input_text = texttospeech.SynthesisInput(text=text.lower().replace('"', ""))
            gender = getattr(
                texttospeech.SsmlVoiceGender,
                self.gender.upper(),
                texttospeech.SsmlVoiceGender.MALE,
            )
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                ssml_gender=gender,
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
            )
            response = client.synthesize_speech(
                input=input_text,
                voice=voice,
                audio_config=audio_config,
            )
            return response.audio_content or None

        return await asyncio.to_thread(_sync_synthesize)


def _voice_file_name(request: ReaderVoiceRequest) -> str:
    safe_entity = re.sub(r"[^a-zA-Z0-9_-]+", "_", request.entity).strip("_") or "voice"
    return f"{safe_entity}_{request.item_id}.mp3"


def _normalise_language_code(language_code: str) -> str:
    value = (language_code or "en-US").strip()
    if "-" in value:
        return value
    return {
        "en": "en-US",
        "ru": "ru-RU",
        "es": "es-ES",
        "fr": "fr-FR",
        "de": "de-DE",
        "it": "it-IT",
        "pt": "pt-PT",
        "nl": "nl-NL",
        "tr": "tr-TR",
        "ja": "ja-JP",
        "ko": "ko-KR",
        "zh": "cmn-CN",
        "ar": "ar-XA",
        "hi": "hi-IN",
        "bn": "bn-IN",
    }.get(value.lower(), value)
