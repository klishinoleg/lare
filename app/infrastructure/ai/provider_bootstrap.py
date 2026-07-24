from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

from application.ai.reader_provider import LocalReaderAiProvider, ReaderAiProvider, set_reader_ai_provider
from core.config import settings
from infrastructure.ai.google_text_to_speech_reader_provider import GoogleTextToSpeechReaderAiProvider
from infrastructure.ai.openai_compatible_reader_provider import OpenAICompatibleReaderAiProvider


OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_DEFAULT_CHAT_MODEL = "deepseek-v4-flash"


def configure_reader_ai_provider(
    *,
    config: Any = settings,
    http_client: httpx.AsyncClient | None = None,
    voice_output_dir: Path | None = None,
) -> ReaderAiProvider:
    provider_name = str(getattr(config, "reader_ai_provider", "local") or "local").lower()
    api_key = str(getattr(config, "reader_ai_openai_api_key", "") or "").strip()
    fallback = LocalReaderAiProvider()

    if provider_name in {"openai", "deepseek"} and api_key:
        provider: ReaderAiProvider = OpenAICompatibleReaderAiProvider(
            api_key=api_key,
            base_url=_base_url(config, provider_name),
            chat_model=_chat_model(config, provider_name),
            image_model=str(getattr(config, "reader_ai_openai_image_model", "dall-e-3") or "dall-e-3"),
            speech_model=str(getattr(config, "reader_ai_openai_speech_model", "tts-1") or "tts-1"),
            speech_voice=str(getattr(config, "reader_ai_openai_speech_voice", "alloy") or "alloy"),
            image_size=str(getattr(config, "reader_ai_openai_image_size", "1024x1024") or "1024x1024"),
            fallback=fallback,
            http_client=http_client,
            voice_output_dir=voice_output_dir,
            provider_name=provider_name,
        )
    else:
        provider = fallback

    voice_provider_name = str(getattr(config, "reader_ai_voice_provider", "") or "").lower()
    if voice_provider_name in {"google", "google_tts", "google-cloud-tts"}:
        google_credentials = str(
            getattr(config, "google_application_credentials", "") or ""
        ).strip()
        if google_credentials:
            os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", google_credentials)
        provider = GoogleTextToSpeechReaderAiProvider(
            fallback=provider,
            language_code=str(
                getattr(config, "reader_ai_google_tts_language_code", "en-US")
                or "en-US"
            ),
            gender=str(getattr(config, "reader_ai_google_tts_gender", "MALE") or "MALE"),
            voice_output_dir=voice_output_dir,
        )

    set_reader_ai_provider(provider)
    return provider


def _base_url(config: Any, provider_name: str) -> str:
    configured = str(getattr(config, "reader_ai_openai_base_url", "") or "").strip()
    if provider_name == "deepseek" and configured in {"", OPENAI_DEFAULT_BASE_URL}:
        return DEEPSEEK_DEFAULT_BASE_URL
    return configured or OPENAI_DEFAULT_BASE_URL


def _chat_model(config: Any, provider_name: str) -> str:
    configured = str(getattr(config, "reader_ai_openai_chat_model", "") or "").strip()
    if provider_name == "deepseek" and configured in {"", "gpt-4o-mini"}:
        return DEEPSEEK_DEFAULT_CHAT_MODEL
    return configured or "gpt-4o-mini"
