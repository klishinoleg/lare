from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from domain.text_data.enums import TextActionsTypes, TextTranslateTypes


@dataclass(slots=True, frozen=True)
class ReaderSegmentRequest:
    account_id: int
    segment_id: int
    ai_log_id: int
    ai_model: str
    text: str
    language_id: int
    action: TextActionsTypes
    translate_type: TextTranslateTypes | None
    query_id: str | None = None
    pid: str | None = None


@dataclass(slots=True, frozen=True)
class ReaderAiProviderResponse:
    content: str
    provider: str = "local"
    file_path: str | None = None


@dataclass(slots=True, frozen=True)
class ReaderTextRequest:
    account_id: int
    text: str
    source_language_code: str | None = None
    target_language_code: str | None = None
    target_language_id: int | None = None
    source_language_id: int | None = None
    purpose: str = "translate"


@dataclass(slots=True, frozen=True)
class ReaderVoiceRequest:
    account_id: int
    entity: str
    item_id: int
    text: str
    fallback_file_path: str
    language_code: str | None = None


@dataclass(slots=True, frozen=True)
class ReaderImageRequest:
    account_id: int
    name: str
    description: str
    fallback_source: str


@dataclass(slots=True, frozen=True)
class ReaderDialogRequest:
    account_id: int
    text_part_id: int
    text_part: str
    message: str
    history: list[dict[str, str]]
    target_language_code: str | None = None


@dataclass(slots=True, frozen=True)
class ReaderWordExplanationRequest:
    account_id: int
    word_id: int
    word: str
    source_language_code: str | None = None
    target_language_code: str | None = None


@dataclass(slots=True, frozen=True)
class ReaderWordExplanationResponse:
    description: str
    root_name: str
    root_description: str
    parts: tuple[dict[str, str], ...] = ()
    provider: str = "local"


class ReaderAiProvider(Protocol):
    async def process_segment(
        self,
        request: ReaderSegmentRequest,
    ) -> ReaderAiProviderResponse:
        ...

    async def translate_text(self, request: ReaderTextRequest) -> ReaderAiProviderResponse:
        ...

    async def create_voice(self, request: ReaderVoiceRequest) -> ReaderAiProviderResponse:
        ...

    async def generate_image(self, request: ReaderImageRequest) -> ReaderAiProviderResponse:
        ...

    async def answer_dialog(self, request: ReaderDialogRequest) -> ReaderAiProviderResponse:
        ...

    async def explain_word(
        self,
        request: ReaderWordExplanationRequest,
    ) -> ReaderWordExplanationResponse:
        ...


class LocalReaderAiProvider:
    async def process_segment(
        self,
        request: ReaderSegmentRequest,
    ) -> ReaderAiProviderResponse:
        if request.action == TextActionsTypes.VOICE:
            file_path = f"uploads/segments/segment-{request.segment_id}.wav"
            return ReaderAiProviderResponse(
                content=file_path,
                provider="local",
                file_path=file_path,
            )
        return ReaderAiProviderResponse(
            content=f"[local] {request.text}",
            provider="local",
        )

    async def translate_text(self, request: ReaderTextRequest) -> ReaderAiProviderResponse:
        suffix = request.target_language_code or str(request.target_language_id or "local")
        compact = " ".join(request.text.split())
        return ReaderAiProviderResponse(content=f"{compact} [{suffix}]", provider="local")

    async def create_voice(self, request: ReaderVoiceRequest) -> ReaderAiProviderResponse:
        return ReaderAiProviderResponse(
            content=request.fallback_file_path,
            provider="local",
            file_path=request.fallback_file_path,
        )

    async def generate_image(self, request: ReaderImageRequest) -> ReaderAiProviderResponse:
        return ReaderAiProviderResponse(content=request.fallback_source, provider="local")

    async def answer_dialog(self, request: ReaderDialogRequest) -> ReaderAiProviderResponse:
        translated = await self.translate_text(
            ReaderTextRequest(
                account_id=request.account_id,
                text=request.message,
                target_language_code=request.target_language_code,
                purpose="dialog",
            )
        )
        return ReaderAiProviderResponse(
            content=f"Local reader note for **{request.text_part}**: {translated.content}",
            provider="local",
        )

    async def explain_word(
        self,
        request: ReaderWordExplanationRequest,
    ) -> ReaderWordExplanationResponse:
        root_name = request.word[: max(1, min(4, len(request.word)))]
        return ReaderWordExplanationResponse(
            description=(
                f"Local explanation for '{request.word}'. "
                "This placeholder keeps the etymology workflow available until AI processing is wired."
            ),
            root_name=root_name,
            root_description=f"Approximate root or base form for '{request.word}'.",
            parts=(
                {
                    "name": root_name,
                    "type": "root",
                    "description": f"Approximate root or base form for '{request.word}'.",
                },
            ),
            provider="local",
        )


_reader_ai_provider: ReaderAiProvider | None = None


def set_reader_ai_provider(provider: ReaderAiProvider | None) -> None:
    global _reader_ai_provider
    _reader_ai_provider = provider


def get_reader_ai_provider() -> ReaderAiProvider:
    if _reader_ai_provider is not None:
        return _reader_ai_provider
    return LocalReaderAiProvider()
