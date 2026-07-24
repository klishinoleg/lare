from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from typing import Any

from application.ai.reader_provider import (
    ReaderAiProvider,
    ReaderAiProviderResponse,
    ReaderDialogRequest,
    ReaderImageRequest,
    ReaderTextRequest,
    ReaderVoiceRequest,
    ReaderWordExplanationRequest,
    ReaderWordExplanationResponse,
)


@dataclass(frozen=True)
class ReaderProviderSmokeStep:
    name: str
    ok: bool
    provider: str | None
    content_length: int
    file_path_present: bool
    data_url_present: bool
    error_message: str | None = None


@dataclass(frozen=True)
class ReaderProviderSmokeResult:
    ok: bool
    include_media: bool
    required_provider: str | None
    steps: tuple[ReaderProviderSmokeStep, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "include_media": self.include_media,
            "required_provider": self.required_provider,
            "steps": [asdict(step) for step in self.steps],
        }


async def run_reader_provider_smoke(
    provider: ReaderAiProvider,
    *,
    include_media: bool = False,
    required_provider: str | None = None,
) -> ReaderProviderSmokeResult:
    required = (required_provider or "").strip().lower() or None
    steps: list[ReaderProviderSmokeStep] = []

    steps.append(
        await _run_response_step(
            name="translate_text",
            call=lambda: provider.translate_text(
                ReaderTextRequest(
                    account_id=0,
                    text="hello world",
                    target_language_code="ru",
                    purpose="smoke",
                )
            ),
            required_provider=required,
        )
    )
    steps.append(
        await _run_response_step(
            name="answer_dialog",
            call=lambda: provider.answer_dialog(
                ReaderDialogRequest(
                    account_id=0,
                    text_part_id=0,
                    text_part="hello world",
                    message="Explain this phrase briefly.",
                    history=[],
                    target_language_code="ru",
                )
            ),
            required_provider=required,
        )
    )
    steps.append(
        await _run_explanation_step(
            name="explain_word",
            call=lambda: provider.explain_word(
                ReaderWordExplanationRequest(
                    account_id=0,
                    word_id=0,
                    word="reader",
                    target_language_code="ru",
                )
            ),
            required_provider=required,
        )
    )

    if include_media:
        steps.append(
            await _run_response_step(
                name="create_voice",
                call=lambda: provider.create_voice(
                    ReaderVoiceRequest(
                        account_id=0,
                        entity="smoke",
                        item_id=0,
                        text="hello world",
                        fallback_file_path="uploads/ai_voice/smoke-local.wav",
                    )
                ),
                required_provider=required,
            )
        )
        steps.append(
            await _run_response_step(
                name="generate_image",
                call=lambda: provider.generate_image(
                    ReaderImageRequest(
                        account_id=0,
                        name="Smoke Test",
                        description="A tiny neutral reading cover for provider validation.",
                        fallback_source="data:image/png;base64,ZmFrZQ==",
                    )
                ),
                required_provider=required,
            )
        )

    return ReaderProviderSmokeResult(
        ok=all(step.ok for step in steps),
        include_media=include_media,
        required_provider=required,
        steps=tuple(steps),
    )


async def _run_response_step(
    *,
    name: str,
    call: Callable[[], Awaitable[ReaderAiProviderResponse]],
    required_provider: str | None,
) -> ReaderProviderSmokeStep:
    try:
        response = await call()
    except Exception as exc:  # noqa: BLE001
        return _failed_step(name=name, error_message=exc.__class__.__name__)

    return _response_step(name=name, response=response, required_provider=required_provider)


async def _run_explanation_step(
    *,
    name: str,
    call: Callable[[], Awaitable[ReaderWordExplanationResponse]],
    required_provider: str | None,
) -> ReaderProviderSmokeStep:
    try:
        response = await call()
    except Exception as exc:  # noqa: BLE001
        return _failed_step(name=name, error_message=exc.__class__.__name__)

    content_length = len(response.description) + len(response.root_name) + len(response.root_description)
    ok = content_length > 0
    error_message = None
    if required_provider and response.provider.lower() != required_provider:
        ok = False
        error_message = f"expected provider {required_provider}, got {response.provider}"
    return ReaderProviderSmokeStep(
        name=name,
        ok=ok,
        provider=response.provider,
        content_length=content_length,
        file_path_present=False,
        data_url_present=False,
        error_message=error_message,
    )


def _response_step(
    *,
    name: str,
    response: ReaderAiProviderResponse,
    required_provider: str | None,
) -> ReaderProviderSmokeStep:
    content = response.content or ""
    ok = bool(content)
    error_message = None
    if required_provider and response.provider.lower() != required_provider:
        ok = False
        error_message = f"expected provider {required_provider}, got {response.provider}"
    return ReaderProviderSmokeStep(
        name=name,
        ok=ok,
        provider=response.provider,
        content_length=len(content),
        file_path_present=bool(response.file_path),
        data_url_present=content.startswith("data:image/"),
        error_message=error_message,
    )


def _failed_step(*, name: str, error_message: str) -> ReaderProviderSmokeStep:
    return ReaderProviderSmokeStep(
        name=name,
        ok=False,
        provider=None,
        content_length=0,
        file_path_present=False,
        data_url_present=False,
        error_message=error_message,
    )
