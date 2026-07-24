from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from application.events.handlers_register.finance import register_finance_main_brokers
from application.ai.reader_provider import (
    LocalReaderAiProvider,
    ReaderAiProviderResponse,
    ReaderDialogRequest,
    ReaderImageRequest,
    ReaderSegmentRequest,
    ReaderTextRequest,
    ReaderVoiceRequest,
    ReaderWordExplanationRequest,
    ReaderWordExplanationResponse,
    set_reader_ai_provider,
)
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.finance.enums.transaction_type import TransactionType
from infrastructure.broker.mock.broker import MockEventBroker
from infrastructure.broker.mock.publisher import MockPublisher
from infrastructure.repository.tortoise.models import (
    AccountModel,
    AccountTransactionModel,
    AccountUsageModel,
    ChapterModel,
    LanguageModel,
    WordTranslateModel,
)
from interfaces.fast_api.routers.compat import (
    _generated_material_from_description,
    _generated_word_count,
)


class FakeBookGenerationProvider:
    def __init__(self) -> None:
        self.purposes: list[str] = []
        self.text_requests: list[ReaderTextRequest] = []
        self.voice_requests: list[ReaderVoiceRequest] = []
        self.word_explanation_requests: list[ReaderWordExplanationRequest] = []

    async def process_segment(self, request: ReaderSegmentRequest) -> ReaderAiProviderResponse:
        return ReaderAiProviderResponse(content=request.text, provider="fake")

    async def translate_text(self, request: ReaderTextRequest) -> ReaderAiProviderResponse:
        self.purposes.append(request.purpose)
        self.text_requests.append(request)
        if request.purpose == "book_generation":
            return ReaderAiProviderResponse(
                content=(
                    '{"title": "La tortue de Toulouse", '
                    '"chapter_text": "La tortue marche dans Toulouse. Elle lit une carte, '
                    'trouve une petite place et parle avec un ami patient."}'
                ),
                provider="fake",
            )
        if request.purpose == "chapter_generation":
            return ReaderAiProviderResponse(
                content=(
                    '{"title": "Le pont du matin", '
                    '"chapter_text": "Le matin, la tortue traverse un pont. '
                    'Elle cherche un cafe calme et apprend trois nouveaux mots."}'
                ),
                provider="fake",
            )
        return ReaderAiProviderResponse(content=request.text, provider="fake")

    async def create_voice(self, request: ReaderVoiceRequest) -> ReaderAiProviderResponse:
        self.voice_requests.append(request)
        relative_file_path = request.fallback_file_path.lstrip("/")
        return ReaderAiProviderResponse(
            content=relative_file_path,
            provider="fake",
            file_path=relative_file_path,
        )

    async def generate_image(self, request: ReaderImageRequest) -> ReaderAiProviderResponse:
        return ReaderAiProviderResponse(content=request.fallback_source, provider="fake")

    async def answer_dialog(self, request: ReaderDialogRequest) -> ReaderAiProviderResponse:
        return ReaderAiProviderResponse(content="dialog", provider="fake")

    async def explain_word(
        self,
        request: ReaderWordExplanationRequest,
    ) -> ReaderWordExplanationResponse:
        self.word_explanation_requests.append(request)
        return ReaderWordExplanationResponse(
            description="description",
            root_name="root",
            root_description="root description",
            provider="fake",
        )


def test_generation_fallback_expands_short_description() -> None:
    title, text = _generated_material_from_description(
        description="Generated reader action chapter prod-cutover.",
        fallback_title="Chapter 2",
        language_code="en",
        book_title="Tom's New Day",
        book_description="A calm family story in Toulouse.",
        existing_chapter_titles=["Tom's New Day"],
    )

    assert title == "Chapter 2"
    assert _generated_word_count(text) >= 80
    assert "prod-cutover" not in text
    assert "Tom's New Day" in text


async def _create_reader_context(
    client: AsyncClient,
    *,
    telegram_id: int = 9103001,
    username: str = "paid_actions",
    account_language_code: str = "en",
    book_language_id: int = 1,
    book_name: str = "Paid actions book",
    chapter_text: str = "hello brave world",
) -> tuple[int, dict[str, str], dict[str, Any]]:
    auth_response = await client.post(
        "/api/v1/account/telegram_auth/",
        json={
            "auth_data": {
                "user": {
                    "id": telegram_id,
                    "username": username,
                    "first_name": "Paid",
                    "last_name": "Actions",
                    "language_code": account_language_code,
                }
            }
        },
    )
    assert auth_response.status_code == 200
    auth_data = auth_response.json()
    account_id = auth_data["account"]["id"]
    headers = {"Authorization": f"Token {auth_data['token']}"}

    book_response = await client.post(
        "/api/v1/book/",
        headers=headers,
        json={"name": book_name, "language": book_language_id},
    )
    assert book_response.status_code == 200
    book_id = book_response.json()["id"]

    add_chapter_response = await client.post(
        f"/api/v1/book/{book_id}/add_chapter/",
        headers=headers,
        json={
            "name": "Paid actions chapter",
            "chapter_input": {"text": chapter_text},
        },
    )
    assert add_chapter_response.status_code == 200
    chapter_id = add_chapter_response.json()["chapters"][0]["id"]

    chapter_response = await client.get(
        f"/api/v1/chapter/{chapter_id}/",
        headers=headers,
    )
    assert chapter_response.status_code == 200
    content = [item for item in chapter_response.json()["content"] if item.get("w")]
    assert len(content) >= 2

    return account_id, headers, {"chapter_id": chapter_id, "content": content}


async def _set_account_credits(account_id: int, credits: Decimal) -> None:
    await AccountTransactionModel.create(
        account_id=account_id,
        transaction_type=TransactionType.MANUAL,
        credits_amount=credits,
    )
    await AccountModel.filter(id=account_id).update(credits=credits)


@pytest.fixture
async def legacy_paid_actions_app(tmp_path):
    db_path = tmp_path / "legacy-paid-actions.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru|fr"
    MockPublisher.clear_events()
    MockEventBroker.subscribers.clear()

    from interfaces.fast_api.main import app

    await init_tortoise()
    register_finance_main_brokers(EventBrokerTypes.MOCK, bills=False)
    try:
        yield app
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_word_etymology_charges_ai_word_usage(
    legacy_paid_actions_app,
) -> None:
    transport = ASGITransport(app=legacy_paid_actions_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        account_id, headers, context = await _create_reader_context(client)
        await _set_account_credits(account_id, Decimal("10.00"))
        word_translate_id = context["content"][0]["w"]

        response = await client.get(
            f"/api/v1/word/{word_translate_id}/create_etymology/",
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json()["ai_word"] is True

    usage = await AccountUsageModel.get(
        account_id=account_id,
        usage_type=AccountUsageType.AI_WORD,
    )
    transaction = await AccountTransactionModel.get(usage_id=usage.id)
    account = await AccountModel.get(id=account_id)

    assert usage.usage_id == word_translate_id
    assert usage.usage_amount == 1
    assert usage.credits_amount == Decimal("10.00")
    assert transaction.credits_amount == Decimal("-10.00")
    assert account.credits == Decimal("0.00")


@pytest.mark.asyncio
async def test_legacy_word_get_etymology_does_not_create_or_charge_ai(
    legacy_paid_actions_app,
) -> None:
    fake_provider = FakeBookGenerationProvider()
    set_reader_ai_provider(fake_provider)
    transport = ASGITransport(app=legacy_paid_actions_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            account_id, headers, context = await _create_reader_context(
                client,
                telegram_id=9103004,
                username="get_etymology_read_only",
            )
            word_id = context["content"][0]["w"]
            language = await LanguageModel.get(code="en")
            word_translate = await WordTranslateModel.create(
                word_id=word_id,
                language_id=language.id,
                account_id=account_id,
                translate="hello",
                transliteration="hello",
                word_type="WRD",
            )

            response = await client.get(
                f"/api/v1/word/{word_id}/get_etymology/",
                headers=headers,
            )
    finally:
        set_reader_ai_provider(None)

    assert response.status_code == 200
    assert response.json()["id"] == word_translate.id
    assert response.json()["ai_word"] is False
    assert fake_provider.word_explanation_requests == []
    assert await AccountUsageModel.filter(account_id=account_id).count() == 0


@pytest.mark.asyncio
async def test_legacy_word_etymology_rejects_non_positive_balance_before_ai(
    legacy_paid_actions_app,
) -> None:
    fake_provider = FakeBookGenerationProvider()
    set_reader_ai_provider(fake_provider)
    transport = ASGITransport(app=legacy_paid_actions_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            account_id, headers, context = await _create_reader_context(
                client,
                telegram_id=9103005,
                username="negative_etymology",
            )
            await _set_account_credits(account_id, Decimal("-1.00"))
            word_translate_id = context["content"][0]["w"]

            response = await client.get(
                f"/api/v1/word/{word_translate_id}/create_etymology/",
                headers=headers,
            )
    finally:
        set_reader_ai_provider(None)

    assert response.status_code == 402
    assert response.json()["detail"] == "Not enough credits."
    assert fake_provider.word_explanation_requests == []
    assert await AccountUsageModel.filter(account_id=account_id).count() == 0


@pytest.mark.asyncio
async def test_legacy_book_cover_generation_charges_ai_image_usage(
    legacy_paid_actions_app,
) -> None:
    transport = ASGITransport(app=legacy_paid_actions_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        account_id, headers, _ = await _create_reader_context(client)
        await _set_account_credits(account_id, Decimal("4.00"))

        response = await client.post(
            "/api/v1/book/generate_image/",
            headers=headers,
            json={
                "name": "A long enough generated cover title",
                "description": "A detailed generated cover prompt for a language practice story.",
            },
        )

    assert response.status_code == 200
    assert response.json()["source"].startswith("data:image/png;base64,")

    usage = await AccountUsageModel.get(
        account_id=account_id,
        usage_type=AccountUsageType.AI_IMAGE,
    )
    transaction = await AccountTransactionModel.get(usage_id=usage.id)
    account = await AccountModel.get(id=account_id)

    assert usage.usage_amount == 1
    assert usage.credits_amount == Decimal("4.00")
    assert transaction.credits_amount == Decimal("-4.00")
    assert account.credits == Decimal("0.00")


@pytest.mark.asyncio
async def test_legacy_ai_book_and_chapter_generation_charge_ai_book_usage(
    legacy_paid_actions_app,
) -> None:
    fake_provider = FakeBookGenerationProvider()
    set_reader_ai_provider(fake_provider)
    transport = ASGITransport(app=legacy_paid_actions_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9103002,
                            "username": "paid_generation",
                            "first_name": "Paid",
                            "last_name": "Generation",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            auth_data = auth_response.json()
            account_id = auth_data["account"]["id"]
            headers = {"Authorization": f"Token {auth_data['token']}"}
            await _set_account_credits(account_id, Decimal("16.00"))

            book_response = await client.post(
                "/api/v1/book/generate/",
                headers=headers,
                json={
                    "language_id": 1,
                    "language_level": "a1",
                    "chapter_type": "story",
                    "description": "A friendly generated story for paid compatibility testing.",
                },
            )
            assert book_response.status_code == 200
            book = book_response.json()["results"][0]
            book_id = book["id"]

            chapter_response = await client.post(
                "/api/v1/book/generate_chapters/",
                headers=headers,
                json={
                    "book_id": book_id,
                    "language_id": 1,
                    "language_level": "a1",
                    "chapter_type": "story",
                    "description": "A short generated follow-up chapter for paid compatibility testing.",
                },
            )
    finally:
        set_reader_ai_provider(None)

    assert chapter_response.status_code == 200
    generated_book = chapter_response.json()
    assert generated_book["id"] == book_id
    assert len(generated_book["chapters"]) == 2
    assert "book_generation" in fake_provider.purposes
    assert "chapter_generation" in fake_provider.purposes
    chapter_prompt = next(
        request.text
        for request in fake_provider.text_requests
        if request.purpose == "chapter_generation"
    )
    assert "Continuity context:" in chapter_prompt
    assert "Book title: La tortue de Toulouse" in chapter_prompt
    assert (
        "Book description/context: A friendly generated story for paid compatibility testing."
        in chapter_prompt
    )
    assert "Existing chapter titles:\n- La tortue de Toulouse" in chapter_prompt
    assert (
        "User request for this chapter: "
        "A short generated follow-up chapter for paid compatibility testing."
        in chapter_prompt
    )

    chapters = await ChapterModel.filter(book_id=book_id).order_by("position", "id")
    assert [chapter.name for chapter in chapters] == [
        "La tortue de Toulouse",
        "Le pont du matin",
    ]
    assert "This local chapter is generated for testing" not in chapters[0].source_url
    assert "This section was generated locally" not in chapters[1].source_url

    usages = await AccountUsageModel.filter(
        account_id=account_id,
        usage_type=AccountUsageType.AI_BOOK,
    ).order_by("id")
    transactions = await AccountTransactionModel.filter(
        account_id=account_id,
        usage_id__in=[usage.id for usage in usages],
    ).order_by("id")
    account = await AccountModel.get(id=account_id)

    assert [usage.usage_id for usage in usages] == [
        book_id,
        generated_book["chapters"][-1]["id"],
    ]
    assert [usage.usage_amount for usage in usages] == [1, 1]
    assert [usage.credits_amount for usage in usages] == [
        Decimal("10.00"),
        Decimal("6.00"),
    ]
    assert [transaction.credits_amount for transaction in transactions] == [
        Decimal("-10.00"),
        Decimal("-6.00"),
    ]
    assert account.credits == Decimal("0.00")


@pytest.mark.asyncio
async def test_legacy_voice_actions_charge_ai_voice_usage(
    legacy_paid_actions_app,
) -> None:
    fake_provider = FakeBookGenerationProvider()
    set_reader_ai_provider(fake_provider)
    transport = ASGITransport(app=legacy_paid_actions_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            account_id, headers, context = await _create_reader_context(client)
            await _set_account_credits(account_id, Decimal("1.00"))
            first_word_translate_id = context["content"][0]["w"]
            word_response = await client.get(
                f"/api/v1/word/{first_word_translate_id}/",
                headers=headers,
            )
            assert word_response.status_code == 200
            word_id = word_response.json()["word"]["id"]

            word_voice_response = await client.post(
                "/api/v1/study_phrase/create_word_voice/",
                headers=headers,
                json={"id": word_id},
            )

            phrase_response = await client.post(
                "/api/v1/phrase/create_from_indexes/",
                headers=headers,
                json={"indexes_list": [[item["id"] for item in context["content"][:2]]]},
            )
            assert phrase_response.status_code == 200
            phrase_id = phrase_response.json()[0]["id"]

            phrase_voice_response = await client.get(
                f"/api/v1/phrase/{phrase_id}/create_voice/",
                headers=headers,
            )
    finally:
        set_reader_ai_provider(None)

    assert word_voice_response.status_code == 200
    assert word_voice_response.json()["ai_voice"]["file"]
    assert word_voice_response.json()["ai_voice"]["file"].startswith("/uploads/")
    assert phrase_voice_response.status_code == 200
    assert phrase_voice_response.json()["ai_voice"]["file"]
    assert phrase_voice_response.json()["ai_voice"]["file"].startswith("/uploads/")

    usages = await AccountUsageModel.filter(
        account_id=account_id,
        usage_type=AccountUsageType.AI_VOICE,
    ).order_by("id")
    transactions = await AccountTransactionModel.filter(
        account_id=account_id,
        usage_id__in=[usage.id for usage in usages],
    ).order_by("id")
    account = await AccountModel.get(id=account_id)

    assert [usage.usage_id for usage in usages] == [word_id, phrase_id]
    assert [usage.usage_amount for usage in usages] == [1, 1]
    assert [usage.credits_amount for usage in usages] == [
        Decimal("0.50"),
        Decimal("0.50"),
    ]
    assert [transaction.credits_amount for transaction in transactions] == [
        Decimal("-0.50"),
        Decimal("-0.50"),
    ]
    assert account.credits == Decimal("0.00")


@pytest.mark.asyncio
async def test_reader_actions_use_book_language_for_deepseek_and_voice(
    legacy_paid_actions_app,
) -> None:
    fake_provider = FakeBookGenerationProvider()
    set_reader_ai_provider(fake_provider)
    transport = ASGITransport(app=legacy_paid_actions_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            languages_response = await client.get("/api/v1/language/")
            assert languages_response.status_code == 200
            languages = languages_response.json()
            french_id = next(item["id"] for item in languages if item["code"] == "fr")

            account_id, headers, context = await _create_reader_context(
                client,
                telegram_id=9103003,
                username="paid_actions_fr",
                account_language_code="ru",
                book_language_id=french_id,
                book_name="Livre francais",
                chapter_text="Nous habitons maintenant a Toulouse.",
            )
            await _set_account_credits(account_id, Decimal("2.00"))
            indexes = [item["id"] for item in context["content"][:2]]

            translate_response = await client.post(
                "/api/v1/text_part/create_from_indexes/",
                headers=headers,
                json={
                    "indexes": indexes,
                    "action": "translate",
                    "translate_type": "translate",
                },
            )
            assert translate_response.status_code == 200
            assert translate_response.json()["words"] == []
            text_part_id = translate_response.json()["id"]

            words_response = await client.post(
                "/api/v1/text_part/create_from_indexes/",
                headers=headers,
                json={
                    "indexes": indexes,
                    "action": "translate",
                    "translate_type": "words",
                },
            )
            assert words_response.status_code == 200
            assert words_response.json()["id"] == text_part_id
            assert words_response.json()["words"]

            voice_response = await client.post(
                "/api/v1/text_part/create_from_indexes/",
                headers=headers,
                json={"indexes": indexes, "action": "create_voice"},
            )
            assert voice_response.status_code == 200

            word_translate_id = context["content"][0]["w"]
            word_response = await client.get(
                f"/api/v1/word/{word_translate_id}/",
                headers=headers,
            )
            assert word_response.status_code == 200
            word_id = word_response.json()["word"]["id"]
            word_voice_response = await client.post(
                "/api/v1/study_phrase/create_word_voice/",
                headers=headers,
                json={"id": word_id},
            )
    finally:
        set_reader_ai_provider(None)

    assert word_voice_response.status_code == 200
    text_request = next(
        request
        for request in fake_provider.text_requests
        if request.purpose == "translate" and "Nous" in request.text
    )
    words_request = next(
        request for request in fake_provider.text_requests if request.purpose == "words"
    )
    assert text_request.source_language_code == "fr"
    assert text_request.target_language_code == "ru"
    assert words_request.source_language_code == "fr"
    assert words_request.target_language_code == "ru"
    assert [request.language_code for request in fake_provider.voice_requests] == [
        "fr",
        "fr",
    ]


@pytest.mark.asyncio
async def test_legacy_voice_actions_do_not_charge_local_fallback(
    legacy_paid_actions_app,
) -> None:
    set_reader_ai_provider(LocalReaderAiProvider())
    transport = ASGITransport(app=legacy_paid_actions_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        account_id, headers, context = await _create_reader_context(client)
        word_translate_id = context["content"][0]["w"]
        word_response = await client.get(
            f"/api/v1/word/{word_translate_id}/",
            headers=headers,
        )
        word_id = word_response.json()["word"]["id"]

        word_voice_response = await client.post(
            "/api/v1/study_phrase/create_word_voice/",
            headers=headers,
            json={"id": word_id},
        )

    assert word_voice_response.status_code == 200
    assert word_voice_response.json()["ai_voice"] is None
    assert (
        await AccountUsageModel.filter(
            account_id=account_id,
            usage_type=AccountUsageType.AI_VOICE,
        ).count()
        == 0
    )
    account = await AccountModel.get(id=account_id)
    assert account.credits == Decimal("0.00")
