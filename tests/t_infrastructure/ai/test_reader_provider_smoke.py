from __future__ import annotations

import pytest

from application.ai.reader_provider import (
    ReaderAiProviderResponse,
    ReaderDialogRequest,
    ReaderImageRequest,
    ReaderTextRequest,
    ReaderVoiceRequest,
    ReaderWordExplanationRequest,
    ReaderWordExplanationResponse,
)


class FakeReaderProvider:
    def __init__(self, provider_name: str = "openai") -> None:
        self.provider_name = provider_name
        self.calls: list[str] = []

    async def translate_text(self, request: ReaderTextRequest) -> ReaderAiProviderResponse:
        self.calls.append("translate_text")
        return ReaderAiProviderResponse(content="translated", provider=self.provider_name)

    async def answer_dialog(self, request: ReaderDialogRequest) -> ReaderAiProviderResponse:
        self.calls.append("answer_dialog")
        return ReaderAiProviderResponse(content="dialog answer", provider=self.provider_name)

    async def explain_word(
        self,
        request: ReaderWordExplanationRequest,
    ) -> ReaderWordExplanationResponse:
        self.calls.append("explain_word")
        return ReaderWordExplanationResponse(
            description="description",
            root_name="read",
            root_description="root",
            provider=self.provider_name,
        )

    async def create_voice(self, request: ReaderVoiceRequest) -> ReaderAiProviderResponse:
        self.calls.append("create_voice")
        return ReaderAiProviderResponse(
            content="uploads/ai_voice/smoke.mp3",
            provider=self.provider_name,
            file_path="uploads/ai_voice/smoke.mp3",
        )

    async def generate_image(self, request: ReaderImageRequest) -> ReaderAiProviderResponse:
        self.calls.append("generate_image")
        return ReaderAiProviderResponse(
            content="data:image/png;base64,ZmFrZQ==",
            provider=self.provider_name,
        )


@pytest.mark.asyncio
async def test_reader_provider_smoke_runs_text_checks_without_leaking_content() -> None:
    from infrastructure.ai.reader_provider_smoke import run_reader_provider_smoke

    provider = FakeReaderProvider(provider_name="openai")

    result = await run_reader_provider_smoke(provider, include_media=False)

    assert result.ok is True
    assert provider.calls == ["translate_text", "answer_dialog", "explain_word"]
    assert [step.name for step in result.steps] == [
        "translate_text",
        "answer_dialog",
        "explain_word",
    ]
    assert result.steps[0].content_length == len("translated")
    assert "translated" not in str(result.to_dict())


@pytest.mark.asyncio
async def test_reader_provider_smoke_can_include_voice_and_image_checks() -> None:
    from infrastructure.ai.reader_provider_smoke import run_reader_provider_smoke

    provider = FakeReaderProvider(provider_name="openai")

    result = await run_reader_provider_smoke(provider, include_media=True)

    assert result.ok is True
    assert provider.calls == [
        "translate_text",
        "answer_dialog",
        "explain_word",
        "create_voice",
        "generate_image",
    ]
    assert result.steps[3].file_path_present is True
    assert result.steps[4].data_url_present is True


@pytest.mark.asyncio
async def test_reader_provider_smoke_fails_when_external_provider_is_required() -> None:
    from infrastructure.ai.reader_provider_smoke import run_reader_provider_smoke

    provider = FakeReaderProvider(provider_name="local")

    result = await run_reader_provider_smoke(
        provider,
        include_media=False,
        required_provider="openai",
    )

    assert result.ok is False
    assert all(step.provider == "local" for step in result.steps)
    assert all(step.ok is False for step in result.steps)
    assert "expected provider openai" in result.steps[0].error_message
