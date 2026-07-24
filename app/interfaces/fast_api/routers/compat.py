from __future__ import annotations

import base64
import binascii
import hashlib
import json
import logging
import math
import re
import unicodedata
import uuid
import wave
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, SuccessfulPayment, WebAppInfo
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status

from application.ai.reader_provider import (
    LocalReaderAiProvider,
    ReaderDialogRequest,
    ReaderImageRequest,
    ReaderTextRequest,
    ReaderVoiceRequest,
    ReaderWordExplanationRequest,
    ReaderAiProvider,
    get_reader_ai_provider,
)
from application.book.events.chapter_events import ChapterCreateRequestedEvent
from application.events.handlers_register.chapter import register_chapter_brokers
from application.finance.dtos.acount_usage import CreateAccountUsageDTO
from application.finance.utils.usage_factory import create_usage_event
from application.security.token import generate_token, verify_token
from application.text.segment.dtos import CreateSegmentByWordChapterIndexesDTO
from application.text.segment.utils.segment_factory import publish_segment_create_request_event
from core.config import settings
from core.di.events import DIPublisher
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.payment.payment_service import PaymentService
from domain.access_role.enums.roles import AccessRole
from domain.account.entities import AccountEntity
from domain.ai.entities import AiModelEntity
from domain.auth_profile.enums import AuthProviderType
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.finance.enums.currency import Currency
from domain.finance.enums.transaction_type import TransactionType
from domain.text_data.enums import TextActionsTypes, TextTranslateTypes
from infrastructure.repository.tortoise.models import (
    AccessRoleModel,
    AccountModel,
    AccountTransactionModel,
    AuthProfileModel,
    BillModel,
    BookModel,
    ChapterModel,
    CompatBookStateModel,
    CompatChapterProgressModel,
    CompatDialogModel,
    CompatPhraseModel,
    CompatPhraseWordModel,
    CompatStudyPhraseLogModel,
    CompatStudyPhraseModel,
    CompatTextPartModel,
    CompatTextPartWordModel,
    CompatWordEtymologyModel,
    CompatWordPartModel,
    LanguageModel,
    WordChapterModel,
    WordModel,
    WordTranslateModel,
    WordVoiceModel,
)
from interfaces.bot.telegram import TelegramBot

router = APIRouter(prefix="/api/v1", tags=["legacy-compatible-api"])
logger = logging.getLogger(__name__)

TOKEN_RE = re.compile(r"\w+(?:[-']\w+)*|[^\w\s]", re.UNICODE)
DATA_URL_RE = re.compile(r"^data:(?P<mime>[-\w/+.;=]+);base64,(?P<data>.+)$", re.DOTALL)
STUDY_PHRASE_LOG_CALLBACK_RE = re.compile(r"^study_phrase_(?P<log_id>\d+)_(?P<rank>\d+)$")
STUDY_TASK_ACTION_CALLBACK_RE = re.compile(r"^action_(?P<action>\d+)$")
MANUAL_BILL_CALLBACK_RE = re.compile(r"^manual_bill_(?P<bill_id>\d+)_(?P<answer>yes|no)$")


@dataclass(frozen=True)
class VoiceFileResult:
    file_path: str
    provider: str

    @property
    def billable(self) -> bool:
        return self.provider.lower() not in {"", "local"}
MANUAL_CREDITS_MESSAGE_RE = re.compile(r"^credits:(?P<account_id>\d+):(?P<credits>\d+):(?P<cost>\d+)(?::(?P<currency>[A-Za-z]{3,4}))?$")
ADMIN_BONUS_MESSAGE_RE = re.compile(
    r"^bonus:(?P<account_id>\d+):(?P<credits>\d+(?:[\.,]\d{1,2})?)$",
    re.IGNORECASE,
)
ADMIN_BONUS_COMMAND_RE = re.compile(
    r"^/(?:bonus|add|credit|credits)(?:@\w+)?\s+"
    r"(?P<account_id>\d+)\s+(?P<credits>\d+(?:[\.,]\d{1,2})?)$",
    re.IGNORECASE,
)
AI_CREDITS_ERROR = "Not enough credits."
ADMIN_CREDIT_COMMANDS = {"/bonus", "/add", "/credit", "/credits"}
HELP_COMMANDS = {"/help", "/commands"}
PUNCT_RE = re.compile(r"^[,.;:!?)]$")
OPEN_PUNCT = {"(", "[", "{", "¿", "¡"}
STUDY_PHRASE_TYPES = {"audio", "forward", "reverse"}
STUDY_TASK_ACTION_TYPES: dict[int, str | None] = {
    0: "audio",
    1: "forward",
    2: "reverse",
    3: None,
}
STUDY_TASK_DELETE_ACTION = 4
BOOK_DESCRIPTIONS_PROFILE_KEY = "compat_book_descriptions"
REFERRAL_PROFILE_KEY = "compat_referral"
REFERRAL_PERCENTAGE = 15
PLACEHOLDER_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)
LEGACY_ACTIONS: dict[str, dict[str, dict[str, Any]]] = {
    "account": {
        "PATCH": {
            "language": {"type": "integer", "required": False, "label": "Language"},
        },
    },
    "book": {
        "POST": {
            "name": {"type": "string", "required": True, "label": "Title"},
            "language": {"type": "integer", "required": True, "label": "Language"},
            "language_id": {"type": "integer", "required": False, "label": "Language"},
            "description": {"type": "string", "required": False, "label": "Description"},
            "image": {"type": "image", "required": False, "label": "Cover"},
            "file": {"type": "file", "required": False, "label": "Cover file"},
        },
        "PATCH": {
            "name": {"type": "string", "required": False, "label": "Title"},
            "language": {"type": "integer", "required": False, "label": "Language"},
            "language_id": {"type": "integer", "required": False, "label": "Language"},
            "description": {"type": "string", "required": False, "label": "Description"},
            "image": {"type": "image", "required": False, "label": "Cover"},
            "file": {"type": "file", "required": False, "label": "Cover file"},
        },
    },
    "chapter": {
        "POST": {
            "name": {"type": "string", "required": True, "label": "Title"},
            "text": {"type": "string", "required": True, "label": "Text"},
            "book": {"type": "integer", "required": True, "label": "Book"},
        },
        "PATCH": {
            "name": {"type": "string", "required": False, "label": "Title"},
            "text": {"type": "string", "required": False, "label": "Text"},
            "percent": {"type": "integer", "required": False, "label": "Progress"},
        },
    },
    "language": {
        "POST": {
            "code": {"type": "string", "required": True, "label": "Code"},
            "name": {"type": "string", "required": True, "label": "Name"},
        },
    },
    "phrase": {
        "POST": {
            "indexes_list": {"type": "list", "required": False, "label": "Word indexes"},
            "action": {"type": "choice", "required": False, "label": "Action"},
        },
    },
    "study_phrase": {
        "POST": {
            "word_translate_id": {"type": "integer", "required": False, "label": "Word"},
            "word_id": {"type": "integer", "required": False, "label": "Word"},
            "text_part_id": {"type": "integer", "required": False, "label": "Text part"},
            "phrase_id": {"type": "integer", "required": False, "label": "Phrase"},
        },
        "PATCH": {
            "is_active": {"type": "boolean", "required": False, "label": "Active"},
            "audio_average": {"type": "float", "required": False, "label": "Audio score"},
            "forward_average": {"type": "float", "required": False, "label": "Forward score"},
            "reverse_average": {"type": "float", "required": False, "label": "Reverse score"},
            "average": {"type": "float", "required": False, "label": "Average score"},
        },
    },
    "text_part": {
        "POST": {
            "indexes": {"type": "list", "required": True, "label": "Word indexes"},
            "translate_type": {"type": "choice", "required": False, "label": "Translate type"},
            "action": {"type": "choice", "required": False, "label": "Action"},
        },
    },
    "transaction": {
        "POST": {
            "cost": {"type": "integer", "required": True, "label": "Stars"},
        },
    },
    "word": {
        "POST": {
            "name": {"type": "string", "required": True, "label": "Word"},
        },
    },
}
DEFAULT_LEGACY_ACTIONS: dict[str, dict[str, Any]] = {
    "POST": {},
    "PATCH": {},
    "PUT": {},
    "DELETE": {},
}

LANGUAGES: tuple[tuple[str, str], ...] = (
    ("en", "English"),
    ("zh", "Chinese"),
    ("es", "Spanish"),
    ("ar", "Arabic"),
    ("hi", "Hindi"),
    ("fr", "French"),
    ("ru", "Russian"),
    ("pt", "Portuguese"),
    ("bn", "Bengali"),
    ("de", "German"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("it", "Italian"),
    ("tr", "Turkish"),
    ("nl", "Dutch"),
)
TEXT_TRANSLATE_TYPE = "translate"
WORDS_TRANSLATE_TYPE = "words"
FULL_TRANSLATE_TYPE = "full"


def _upload_url() -> str:
    return settings.images_upload_url or "uploads"


def _public_upload_path(*parts: str) -> str:
    clean_parts = [part.strip("/\\") for part in parts if part]
    return "/" + "/".join([_upload_url(), *clean_parts])


def _public_file_path(value: str | None) -> str | None:
    if not value:
        return None
    normalized = str(value).replace("\\", "/")
    if normalized.startswith(("/", "http://", "https://", "data:")):
        return normalized
    return f"/{normalized.lstrip('/')}"


def _truthy(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _first_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _truncate(value: str, length: int) -> str:
    value = value.strip()
    return value[:length] if len(value) > length else value


def _is_word_token(value: str) -> bool:
    return any(ch.isalnum() for ch in value)


def _segment_action(value: Any) -> TextActionsTypes:
    value_str = str(value or "").lower()
    if value_str in {"create_voice", "voice", TextActionsTypes.VOICE.value.lower()}:
        return TextActionsTypes.VOICE
    return TextActionsTypes.TRANSLATE


def _segment_translate_type(value: Any) -> TextTranslateTypes | None:
    value_str = str(value or "").lower()
    mapping = {
        "translate": TextTranslateTypes.TEXT,
        "text": TextTranslateTypes.TEXT,
        "words": TextTranslateTypes.WORDS,
        "full": TextTranslateTypes.FULL,
    }
    return mapping.get(value_str)


def _compat_translate_type(value: Any) -> str:
    value_str = str(value or "").lower()
    if value_str in {"words", TextTranslateTypes.WORDS.value.lower()}:
        return WORDS_TRANSLATE_TYPE
    if value_str in {"full", TextTranslateTypes.FULL.value.lower()}:
        return FULL_TRANSLATE_TYPE
    return TEXT_TRANSLATE_TYPE


def _translate_type_needs_text(translate_type: str) -> bool:
    return translate_type in {TEXT_TRANSLATE_TYPE, FULL_TRANSLATE_TYPE}


def _translate_type_needs_words(translate_type: str) -> bool:
    return translate_type in {WORDS_TRANSLATE_TYPE, FULL_TRANSLATE_TYPE}


def _account_entity(account: AccountModel) -> AccountEntity:
    return AccountEntity(
        id=account.id,
        username=account.username,
        public_name=account.public_name,
        email=account.email,
        credits=account.credits,
        is_active=account.is_active,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


def _local_ai_model(action: TextActionsTypes) -> AiModelEntity:
    usage_type = AccountUsageType.AI_VOICE if action == TextActionsTypes.VOICE else AccountUsageType.AI_TRANSLATE
    return AiModelEntity(
        name="Local compatibility model",
        model="local-compat",
        input_cost=Decimal("0"),
        output_cost=Decimal("0"),
        kef=1,
        allow_to=[usage_type],
    )


def _account_credits_decimal(account: AccountModel) -> Decimal:
    return Decimal(str(account.credits or 0))


async def _assert_ai_credits(
    account: AccountModel,
    required: Decimal = Decimal("0"),
) -> None:
    fresh = await AccountModel.get(id=account.id)
    account.credits = fresh.credits
    balance = _account_credits_decimal(fresh)
    required_amount = Decimal(str(required or 0))
    if balance <= 0 or (required_amount > 0 and balance < required_amount):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=AI_CREDITS_ERROR,
        )


async def _reader_ai_provider_for_account(
    account: AccountModel,
    required: Decimal = Decimal("0"),
) -> ReaderAiProvider:
    provider = get_reader_ai_provider()
    if not isinstance(provider, LocalReaderAiProvider):
        await _assert_ai_credits(account, required)
    return provider


async def _charge_compat_usage(
    *,
    account: AccountModel,
    usage_type: AccountUsageType,
    usage_id: int,
    credits_amount: Decimal,
    usage_amount: int = 1,
) -> None:
    await _assert_ai_credits(account, credits_amount)
    await create_usage_event(
        CreateAccountUsageDTO(
            account_id=account.id,
            usage_type=usage_type,
            usage_id=usage_id,
            usage_amount=usage_amount,
            credits_amount=credits_amount,
        )
    )


def _join_tokens(tokens: list[str]) -> str:
    result = ""
    previous = ""
    for token in tokens:
        if not result:
            result = token
        elif PUNCT_RE.match(token) or previous in OPEN_PUNCT:
            result += token
        else:
            result += f" {token}"
        previous = token
    return result.strip()


def _fake_translate(value: str, language: LanguageModel | None = None) -> str:
    suffix = language.code if language else settings.default_language
    compact = " ".join(value.split())
    return f"{compact} [{suffix}]"


async def _translate_text(
    value: str,
    account: AccountModel,
    language: LanguageModel | None = None,
    purpose: str = "translate",
    source_language: LanguageModel | None = None,
) -> str:
    target_language = language or await _target_language(account)
    provider = await _reader_ai_provider_for_account(account)
    response = await provider.translate_text(
        ReaderTextRequest(
            account_id=account.id,
            text=value,
            source_language_code=source_language.code if source_language else None,
            source_language_id=source_language.id if source_language else None,
            target_language_code=target_language.code,
            target_language_id=target_language.id,
            purpose=purpose,
        )
    )
    parsed = _json_object_from_ai_response(response.content)
    translated = parsed.get("translate")
    if isinstance(translated, str) and translated.strip():
        return translated.strip()
    return response.content


def _json_object_from_ai_response(value: str) -> dict[str, Any]:
    compact = value.strip()
    if compact.startswith("```"):
        compact = re.sub(r"^```(?:json)?\s*", "", compact, flags=re.IGNORECASE)
        compact = re.sub(r"\s*```$", "", compact)
    match = re.search(r"\{.*\}", compact, flags=re.DOTALL)
    if match:
        compact = match.group(0)
    try:
        parsed = json.loads(compact)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _normalise_word_lookup(value: str) -> str:
    compact = str(value or "").strip().lower()
    compact = re.sub(r"^[^\w]+|[^\w]+$", "", compact, flags=re.UNICODE)
    compact = unicodedata.normalize("NFKD", compact)
    compact = "".join(char for char in compact if not unicodedata.combining(char))
    return compact


def _normalise_word_type(value: Any) -> str:
    compact = str(value or "").strip().upper()
    return _truncate(compact or "WRD", 64)


def _normalise_gender(value: Any) -> str | None:
    compact = str(value or "").strip().lower()
    return compact if compact in {"m", "f", "n"} else None


async def _word_table_from_ai(
    *,
    text: str,
    account: AccountModel,
    source_language: LanguageModel,
    target_language: LanguageModel,
    translate_type: str,
) -> tuple[str | None, list[dict[str, Any]]]:
    provider = await _reader_ai_provider_for_account(account)
    response = await provider.translate_text(
        ReaderTextRequest(
            account_id=account.id,
            text=text,
            source_language_code=source_language.code,
            source_language_id=source_language.id,
            target_language_code=target_language.code,
            target_language_id=target_language.id,
            purpose=translate_type,
        )
    )
    parsed = _json_object_from_ai_response(response.content)
    table_raw = parsed.get("table")
    table = [item for item in table_raw if isinstance(item, dict)] if isinstance(table_raw, list) else []
    translated = parsed.get("translate")
    return (translated.strip() if isinstance(translated, str) and translated.strip() else None), table


async def _ensure_word_translate_from_ai_row(
    *,
    word: WordModel,
    account: AccountModel,
    target_language: LanguageModel,
    row: dict[str, Any],
) -> WordTranslateModel:
    translate = _truncate(str(row.get("translate") or "").strip(), 512)
    if not translate:
        translate = await _translate_text(
            word.name,
            account,
            target_language,
            purpose="word",
            source_language=await LanguageModel.get(id=word.language_id),
        )
    obj = await WordTranslateModel.get_or_none(
        word_id=word.id,
        language_id=target_language.id,
        account_id=account.id,
    )
    values = {
        "translate": _truncate(translate, 512),
        "transliteration": _truncate(str(row.get("translit") or "").strip(), 255) or None,
        "word_type": _normalise_word_type(row.get("type")),
        "gender": _normalise_gender(row.get("gender")),
    }
    if obj:
        obj.translate = values["translate"]
        obj.transliteration = values["transliteration"]
        obj.word_type = values["word_type"]
        obj.gender = values["gender"]
        await obj.save()
        return obj
    return await WordTranslateModel.create(
        word_id=word.id,
        language_id=target_language.id,
        account_id=account.id,
        **values,
    )


async def _ensure_word_translates_for_selected_links(
    *,
    links: list[CompatTextPartWordModel] | list[CompatPhraseWordModel],
    account: AccountModel,
    source_language: LanguageModel,
    target_language: LanguageModel,
    text: str,
    translate_type: str = WORDS_TRANSLATE_TYPE,
) -> str | None:
    translated_text, table = await _word_table_from_ai(
        text=text,
        account=account,
        source_language=source_language,
        target_language=target_language,
        translate_type=translate_type,
    )
    word_chapters = [
        await WordChapterModel.get(id=link.word_chapter_id)
        for link in links
    ]
    words_by_lookup: dict[str, WordModel] = {}
    for word_chapter in word_chapters:
        word = await WordModel.get(id=word_chapter.word_id)
        words_by_lookup[_normalise_word_lookup(word_chapter.name)] = word
        words_by_lookup[_normalise_word_lookup(word.name)] = word

    handled_word_ids: set[int] = set()
    for row in table:
        lookup = _normalise_word_lookup(str(row.get("word") or ""))
        word = words_by_lookup.get(lookup)
        if not word:
            continue
        await _ensure_word_translate_from_ai_row(
            word=word,
            account=account,
            target_language=target_language,
            row=row,
        )
        handled_word_ids.add(word.id)

    for word_chapter in word_chapters:
        word = await WordModel.get(id=word_chapter.word_id)
        if word.id in handled_word_ids or not _is_word_token(word_chapter.name):
            continue
        await _ensure_word_translate(
            word,
            account,
            target_language,
            source_language=source_language,
        )

    return translated_text


def _generated_material_from_description(
    *,
    description: str,
    fallback_title: str,
    language_code: str | None = None,
    book_title: str | None = None,
    book_description: str | None = None,
    existing_chapter_titles: list[str] | None = None,
) -> tuple[str, str]:
    subject = _generation_fallback_subject(description, fallback_title)
    title = _truncate(subject.split(".")[0].strip() or fallback_title, 255)
    text = _normalise_generated_chapter_text(description)
    if _generated_word_count(text) < 80:
        text = _fallback_chapter_text(
            subject=subject,
            fallback_title=fallback_title,
            language_code=language_code,
            book_title=book_title,
            book_description=book_description,
            existing_chapter_titles=existing_chapter_titles,
        )
    return title, text


def _generation_fallback_subject(description: str, fallback_title: str) -> str:
    subject = " ".join(str(description or "").split())
    if re.search(
        r"\b(test|smoke|mock|cutover|implementation|lazy\s*reader|prod-)",
        subject,
        flags=re.IGNORECASE,
    ):
        subject = ""
    return _truncate(subject or fallback_title or "A simple new chapter", 255)


def _fallback_chapter_text(
    *,
    subject: str,
    fallback_title: str,
    language_code: str | None = None,
    book_title: str | None = None,
    book_description: str | None = None,
    existing_chapter_titles: list[str] | None = None,
) -> str:
    code = (language_code or "en").lower()
    compact_book_title = " ".join(str(book_title or "").split())
    compact_description = " ".join(str(book_description or "").split())
    previous_title = next(
        (
            " ".join(str(title or "").split())
            for title in (existing_chapter_titles or [])
            if " ".join(str(title or "").split())
        ),
        "",
    )
    topic = subject or fallback_title or compact_book_title or "the day"
    if code.startswith("fr"):
        sentences = [
            f"{topic} commence doucement.",
            "Le matin est calme, et les personnages regardent autour d'eux.",
            "Ils parlent avec des phrases simples.",
            "Chaque personne ecoute avec attention.",
            "La rue est claire, et la ville semble proche.",
            "Un ami pose une question courte.",
            "Un autre ami repond avec patience.",
            "Ils marchent ensemble et remarquent de petits details.",
            "Le contexte du livre reste present dans chaque scene.",
            f"Le livre s'appelle {compact_book_title}." if compact_book_title else "",
            f"L'idee principale est {compact_description}." if compact_description else "",
            f"Le chapitre precedent etait {previous_title}." if previous_title else "",
            "Maintenant, l'histoire continue sans repeter le meme moment.",
            "Les mots sont faciles, mais la situation avance.",
            "Il y a un lieu, une action, et une petite decision.",
            "Les personnages veulent comprendre ce qui change.",
            "Ils observent une porte, une table, une lumiere, et un chemin.",
            "Une phrase nouvelle donne une direction.",
            "Le dialogue reste court et naturel.",
            "Les emotions sont calmes et visibles.",
            "Quelqu'un sourit, puis propose une idee.",
            "Tout le monde accepte d'essayer.",
            "Ils font un pas, puis un autre.",
            "La scene devient plus vivante.",
            "A la fin, ils apprennent un mot utile.",
            "Ils gardent ce mot pour la prochaine rencontre.",
            "Le chapitre se termine avec une petite question.",
            "Cette question ouvre la suite de l'histoire.",
        ]
    elif code.startswith("ru"):
        sentences = [
            f"{topic} начинается спокойно.",
            "Утро тихое, и герои смотрят вокруг.",
            "Они говорят короткими фразами.",
            "Каждый слушает внимательно.",
            "Город рядом, и дорога кажется понятной.",
            "Один друг задает простой вопрос.",
            "Другой отвечает терпеливо.",
            "Они идут вместе и замечают маленькие детали.",
            "Контекст книги остается в каждой сцене.",
            f"Книга называется {compact_book_title}." if compact_book_title else "",
            f"Главная идея такая: {compact_description}." if compact_description else "",
            f"Прошлая глава называлась {previous_title}." if previous_title else "",
            "Теперь история продолжается и не повторяет тот же момент.",
            "Слова простые, но ситуация движется вперед.",
            "Есть место, действие и маленькое решение.",
            "Герои хотят понять, что меняется.",
            "Они видят дверь, стол, свет и дорогу.",
            "Новая фраза дает направление.",
            "Диалог остается коротким и естественным.",
            "Эмоции спокойные и понятные.",
            "Кто-то улыбается и предлагает идею.",
            "Все решают попробовать.",
            "Они делают один шаг, потом другой.",
            "Сцена становится живее.",
            "В конце они учат полезное слово.",
            "Они сохраняют это слово для следующей встречи.",
            "Глава заканчивается маленьким вопросом.",
            "Этот вопрос открывает продолжение истории.",
        ]
    else:
        sentences = [
            f"{topic} begins in a quiet way.",
            "The morning is calm, and the characters look around.",
            "They speak with short and clear sentences.",
            "Each person listens carefully.",
            "The street is bright, and the place feels close.",
            "One friend asks a simple question.",
            "Another friend answers with patience.",
            "They walk together and notice small details.",
            "The context of the book stays inside the scene.",
            f"The book is called {compact_book_title}." if compact_book_title else "",
            f"The main idea is {compact_description}." if compact_description else "",
            f"The previous chapter was {previous_title}." if previous_title else "",
            "Now the story continues without repeating the same moment.",
            "The words are easy, but the situation moves forward.",
            "There is a place, an action, and a small decision.",
            "The characters want to understand what is changing.",
            "They see a door, a table, a light, and a path.",
            "A new sentence gives them a direction.",
            "The dialogue stays short and natural.",
            "The emotions are calm and easy to see.",
            "Someone smiles and suggests an idea.",
            "Everyone agrees to try.",
            "They take one step and then another step.",
            "The scene becomes more alive.",
            "At the end, they learn a useful word.",
            "They keep this word for the next meeting.",
            "The chapter ends with a small question.",
            "This question opens the next part of the story.",
        ]
    text = " ".join(sentence for sentence in sentences if sentence)
    return _truncate(text, 8000)


def _normalise_generated_chapter_text(value: str) -> str:
    lines = [" ".join(line.split()) for line in str(value or "").splitlines()]
    compact_lines = [line for line in lines if line]
    text = "\n".join(compact_lines) if compact_lines else " ".join(str(value or "").split())
    return _truncate(text, 8000)


def _generated_word_count(value: str) -> int:
    return len(re.findall(r"[^\W\d_]+(?:['’-][^\W\d_]+)?", value, flags=re.UNICODE))


def _reader_generation_context(
    *,
    book_title: str | None = None,
    book_description: str | None = None,
    existing_chapter_titles: list[str] | None = None,
) -> str:
    lines: list[str] = []
    compact_title = " ".join(str(book_title or "").split())
    if compact_title:
        lines.append(f"Book title: {_truncate(compact_title, 255)}")

    compact_description = " ".join(str(book_description or "").split())
    if compact_description:
        lines.append(f"Book description/context: {_truncate(compact_description, 2000)}")

    titles = [
        _truncate(" ".join(str(title or "").split()), 255)
        for title in (existing_chapter_titles or [])
    ]
    titles = [title for title in titles if title]
    if titles:
        visible_titles = titles[:20]
        lines.append("Existing chapter titles:")
        lines.extend(f"- {title}" for title in visible_titles)
        if len(titles) > len(visible_titles):
            lines.append(f"... and {len(titles) - len(visible_titles)} more")

    return "\n".join(lines)


async def _generate_reader_chapter_material(
    *,
    account: AccountModel,
    language: LanguageModel,
    description: str,
    language_level: str,
    chapter_type: str,
    purpose: str,
    fallback_title: str,
    book_title: str | None = None,
    book_description: str | None = None,
    existing_chapter_titles: list[str] | None = None,
) -> tuple[str, str]:
    context = _reader_generation_context(
        book_title=book_title,
        book_description=book_description,
        existing_chapter_titles=existing_chapter_titles,
    )
    prompt_parts = [
        "Create reading material for a language learner. "
        "Return JSON only with keys title and chapter_text.",
        f"Target language code: {language.code}",
        f"Language level: {language_level or 'a1'}",
        f"Chapter type: {chapter_type or 'story'}",
        "Length: 320-420 words. Write at least 30 short sentences. "
        "Use plain, learner-friendly sentences and split the text into 4-6 short paragraphs. "
        "Do not mention tests, mocks, implementation details, or Lazy Reader.",
    ]
    if context:
        prompt_parts.extend(
            [
                "Continuity context:",
                context,
                "Use the context to continue the same book. "
                "Do not repeat an existing chapter title.",
            ]
        )
    prompt_parts.append(f"User request for this chapter: {description}")
    prompt = "\n".join(prompt_parts)
    provider = await _reader_ai_provider_for_account(account)
    response = await provider.translate_text(
        ReaderTextRequest(
            account_id=account.id,
            text=prompt,
            target_language_code=language.code,
            target_language_id=language.id,
            purpose=purpose,
        )
    )
    parsed = _json_object_from_ai_response(response.content)
    title = _truncate(str(parsed.get("title") or "").strip(), 255)
    chapter_text = _normalise_generated_chapter_text(parsed.get("chapter_text") or "")
    if title and chapter_text and _generated_word_count(chapter_text) < 260:
        chapter_text = await _expand_reader_chapter_text(
            account=account,
            language=language,
            title=title,
            chapter_text=chapter_text,
            language_level=language_level,
            chapter_type=chapter_type,
            purpose=purpose,
            book_title=book_title,
            book_description=book_description,
            existing_chapter_titles=existing_chapter_titles,
        )
    if title and chapter_text and _generated_word_count(chapter_text) >= 80:
        return title, chapter_text
    if title and chapter_text:
        return title, _fallback_chapter_text(
            subject=title,
            fallback_title=fallback_title,
            language_code=language.code,
            book_title=book_title,
            book_description=book_description,
            existing_chapter_titles=existing_chapter_titles,
        )
    return _generated_material_from_description(
        description=description,
        fallback_title=fallback_title,
        language_code=language.code,
        book_title=book_title,
        book_description=book_description,
        existing_chapter_titles=existing_chapter_titles,
    )


async def _expand_reader_chapter_text(
    *,
    account: AccountModel,
    language: LanguageModel,
    title: str,
    chapter_text: str,
    language_level: str,
    chapter_type: str,
    purpose: str,
    book_title: str | None = None,
    book_description: str | None = None,
    existing_chapter_titles: list[str] | None = None,
) -> str:
    context = _reader_generation_context(
        book_title=book_title,
        book_description=book_description,
        existing_chapter_titles=existing_chapter_titles,
    )
    prompt_parts = [
        "Expand this language-learning chapter. "
        "Return JSON only with key chapter_text.",
        f"Target language code: {language.code}",
        f"Language level: {language_level or 'a1'}",
        f"Chapter type: {chapter_type or 'story'}",
        f"Title: {title}",
        "Required length: 320-420 words, at least 30 short sentences, 4-6 short paragraphs. "
        "Keep the same topic and simple learner-friendly language.",
    ]
    if context:
        prompt_parts.extend(["Continuity context:", context])
    prompt_parts.append(f"Current chapter_text: {chapter_text}")
    prompt = "\n".join(prompt_parts)
    provider = await _reader_ai_provider_for_account(account)
    response = await provider.translate_text(
        ReaderTextRequest(
            account_id=account.id,
            text=prompt,
            target_language_code=language.code,
            target_language_id=language.id,
            purpose=f"{purpose}_expand",
        )
    )
    parsed = _json_object_from_ai_response(response.content)
    expanded = _normalise_generated_chapter_text(parsed.get("chapter_text") or "")
    return expanded or chapter_text


def _fake_transliteration(value: str) -> str:
    return " ".join(value.lower().split())[:255]


def _local_voice_file_path(entity: str, item_id: int, text: str) -> str:
    voice_dir = settings.get_upload_dir() / "compat_voice"
    voice_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{entity}_{item_id}.wav"
    local_path = voice_dir / file_name
    if not local_path.exists():
        _write_silent_wav(local_path, text)
    return _public_upload_path("compat_voice", file_name)


async def _voice_file_result(
    entity: str,
    item_id: int,
    text: str,
    account: AccountModel,
    language: LanguageModel | None = None,
    required_credits: Decimal = Decimal("0"),
) -> VoiceFileResult:
    fallback_file_path = _local_voice_file_path(entity, item_id, text)
    voice_language = language or await _target_language(account)
    provider = await _reader_ai_provider_for_account(account, required_credits)
    response = await provider.create_voice(
        ReaderVoiceRequest(
            account_id=account.id,
            entity=entity,
            item_id=item_id,
            text=text,
            fallback_file_path=fallback_file_path,
            language_code=voice_language.code,
        )
    )
    return VoiceFileResult(
        file_path=response.file_path or response.content or fallback_file_path,
        provider=response.provider or "local",
    )


async def _voice_file_path(
    entity: str,
    item_id: int,
    text: str,
    account: AccountModel,
    language: LanguageModel | None = None,
) -> str:
    result = await _voice_file_result(entity, item_id, text, account, language)
    return result.file_path


def _write_silent_wav(path: Path, text: str) -> None:
    duration_seconds = min(max(len(text) / 80, 0.35), 1.2)
    frame_rate = 16_000
    frames = max(1, math.ceil(frame_rate * duration_seconds))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(frame_rate)
        wav.writeframes(b"\x00\x00" * frames)


def _placeholder_image_path() -> str:
    image_dir = settings.get_upload_dir() / "compat"
    image_dir.mkdir(parents=True, exist_ok=True)
    image_path = image_dir / "book-placeholder.svg"
    if not image_path.exists():
        image_path.write_text(
            (
                '<svg xmlns="http://www.w3.org/2000/svg" width="360" height="540" '
                'viewBox="0 0 360 540"><rect width="360" height="540" fill="#243447"/>'
                '<rect x="54" y="58" width="252" height="424" rx="18" fill="#f4d35e"/>'
                '<text x="180" y="276" text-anchor="middle" font-size="34" '
                'font-family="Arial" fill="#243447">Lazy Reader</text></svg>'
            ),
            encoding="utf-8",
        )
    return _public_upload_path("compat", "book-placeholder.svg")


def _image_path_from_payload(payload: dict[str, Any]) -> str:
    image = payload.get("image")
    if isinstance(image, str):
        return image if image.startswith("/") else ""
    if not isinstance(image, dict):
        return ""
    content = str(image.get("content") or image.get("source") or "")
    match = DATA_URL_RE.match(content)
    if not match:
        return ""
    mime = match.group("mime").lower()
    extension = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/webp": "webp",
        "image/svg+xml": "svg",
    }.get(mime, "png")
    try:
        raw = base64.b64decode(match.group("data"), validate=True)
    except (binascii.Error, ValueError):
        return ""
    image_dir = settings.get_upload_dir() / "compat_books"
    image_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid.uuid4().hex}.{extension}"
    (image_dir / file_name).write_bytes(raw)
    return _public_upload_path("compat_books", file_name)


def _source_url_from_payload(payload: dict[str, Any]) -> str:
    chapter_input = payload.get("chapter_input") if isinstance(payload, dict) else {}
    if not isinstance(chapter_input, dict):
        chapter_input = {}
    source_url = (
        payload.get("source_url")
        or payload.get("input_url")
        or payload.get("url")
        or chapter_input.get("source_url")
        or chapter_input.get("input_url")
        or chapter_input.get("url")
        or ""
    )
    return _truncate(str(source_url).strip(), 500)


def _payload_has_source_url(payload: dict[str, Any]) -> bool:
    if any(key in payload for key in ("source_url", "input_url", "url")):
        return True
    chapter_input = payload.get("chapter_input")
    return isinstance(chapter_input, dict) and any(
        key in chapter_input for key in ("source_url", "input_url", "url")
    )


async def _ensure_languages() -> None:
    if await LanguageModel.all().count() > 0:
        return
    configured = settings.get_languages()
    source = configured if configured else LANGUAGES
    for ordering, (code, name) in enumerate(source, start=1):
        await LanguageModel.get_or_create(
            slug=code,
            defaults={
                "name": name,
                "code": code,
                "original_name": name,
                "ordering": ordering,
            },
        )


async def _current_account(request: Request) -> AccountModel:
    authorization = request.headers.get("Authorization") or ""
    token = ""
    if authorization.lower().startswith("token "):
        token = authorization.split(" ", 1)[1].strip()
    elif authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif authorization:
        token = authorization.strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    account_id = verify_token(token)
    if not account_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    account = await AccountModel.get_or_none(id=account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return account


async def _telegram_profile(account: AccountModel) -> AuthProfileModel | None:
    return await AuthProfileModel.get_or_none(
        account_id=account.id,
        provider_type=AuthProviderType.TELEGRAM,
    )


async def _target_language(account: AccountModel) -> LanguageModel:
    await _ensure_languages()
    profile = await _telegram_profile(account)
    data = profile.provider_data if profile else {}
    language_id = _safe_int(data.get("language_id"))
    if language_id:
        language = await LanguageModel.get_or_none(id=language_id)
        if language:
            return language
    if profile and profile.language_code:
        language = await LanguageModel.get_or_none(code=profile.language_code)
        if language:
            return language
    language = await LanguageModel.get_or_none(code=settings.default_language)
    return language or await LanguageModel.all().first()


async def _book_language(book: BookModel) -> LanguageModel:
    language = await LanguageModel.get_or_none(id=book.language_id)
    if language:
        return language
    await _ensure_languages()
    return await LanguageModel.all().first()


async def _word_language_from_chapter(chapter: ChapterModel) -> LanguageModel:
    book = await BookModel.get(id=chapter.book_id)
    return await _book_language(book)


async def _paginate(query: Any, page: int | None = None, per_page: int = 10) -> dict[str, Any]:
    count = await query.count()
    if page and page > 0:
        query = query.offset((page - 1) * per_page).limit(per_page)
    items = await query
    return {"count": count, "results": items}


def _paginate_sequence(items: list[Any], page: int | None = None, per_page: int = 10) -> dict[str, Any]:
    if page and page > 0:
        start = (page - 1) * per_page
        return {"count": len(items), "results": items[start : start + per_page]}
    return {"count": len(items), "results": items}


async def _book_state(book: BookModel, account: AccountModel) -> CompatBookStateModel:
    state_obj, _ = await CompatBookStateModel.get_or_create(
        account_id=account.id,
        book_id=book.id,
        defaults={"is_active": True},
    )
    return state_obj


async def _book_is_active(book: BookModel, account: AccountModel) -> bool:
    state_obj = await CompatBookStateModel.get_or_none(account_id=account.id, book_id=book.id)
    return state_obj.is_active if state_obj else True


async def _book_description(book: BookModel, account: AccountModel) -> str:
    description = getattr(book, "description", None)
    if description:
        return str(description)
    profile = await _telegram_profile(account)
    data = profile.provider_data if profile else {}
    descriptions = data.get(BOOK_DESCRIPTIONS_PROFILE_KEY) if isinstance(data, dict) else {}
    if not isinstance(descriptions, dict):
        return ""
    return str(descriptions.get(str(book.id)) or "")


async def _set_book_description(book: BookModel, account: AccountModel, description: str | None) -> None:
    profile = await _telegram_profile(account)
    if not profile:
        return
    data = dict(profile.provider_data or {})
    descriptions = data.get(BOOK_DESCRIPTIONS_PROFILE_KEY)
    if not isinstance(descriptions, dict):
        descriptions = {}
    descriptions[str(book.id)] = description or ""
    data[BOOK_DESCRIPTIONS_PROFILE_KEY] = descriptions
    profile.provider_data = data
    await profile.save()


async def _filter_books_by_active(
    books: list[BookModel],
    account: AccountModel,
    is_active: bool,
) -> list[BookModel]:
    result = []
    for book in books:
        if await _book_is_active(book, account) is is_active:
            result.append(book)
    return result


async def _serialize_language(language: LanguageModel) -> dict[str, Any]:
    return {
        "id": language.id,
        "name": language.name,
        "slug": language.slug,
        "code": language.code,
        "original_name": language.original_name,
        "ordering": language.ordering,
    }


async def _serialize_account(account: AccountModel) -> dict[str, Any]:
    profile = await _telegram_profile(account)
    data = profile.provider_data if profile else {}
    user = data.get("user") or data.get("auth_data", {}).get("user") or {}
    language = await _target_language(account)
    full_name = account.public_name or " ".join(
        part for part in [user.get("first_name"), user.get("last_name")] if part
    )
    return {
        "id": account.id,
        "username": account.username,
        "email": account.email,
        "public_name": account.public_name,
        "full_name": full_name or account.username,
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "avatar": user.get("photo_url") or data.get("photo_url"),
        "credits": float(account.credits or 0),
        "tg_user_id": _safe_int(user.get("id") or data.get("tg_user_id")),
        "tg_language_code": user.get("language_code") or (profile.language_code if profile else None),
        "language_id": language.id if language else None,
        "ai_type": data.get("ai_type") or "local",
        "use_google_translate": _truthy(data.get("use_google_translate"), True),
        "is_active": account.is_active,
    }


async def _serialize_word_model(word: WordModel, account: AccountModel) -> dict[str, Any]:
    voice = await WordVoiceModel.get_or_none(word_id=word.id)
    etymology = await CompatWordEtymologyModel.get_or_none(word_id=word.id)
    parts = []
    if etymology:
        part_models = await CompatWordPartModel.filter(etymology_id=etymology.id).order_by("id")
        parts = [
            {
                "id": part.id,
                "name": part.name,
                "type": part.part_type,
                "translate": {"description": part.description or ""},
            }
            for part in part_models
        ]
    return {
        "id": word.id,
        "name": word.name,
        "ai_voice": (
            {"id": voice.id, "file": _public_file_path(voice.file_path)}
            if voice
            else None
        ),
        "etymology": {"description": etymology.description} if etymology else None,
        "root": (
            {
                "id": etymology.id,
                "name": etymology.root_name,
                "translate": {"description": etymology.root_description or ""},
            }
            if etymology
            else None
        ),
        "word_parts": parts,
        "related_words": [],
    }


async def _ensure_word_translate(
    word: WordModel,
    account: AccountModel,
    language: LanguageModel | None = None,
    source_language: LanguageModel | None = None,
) -> WordTranslateModel:
    target_language = language or await _target_language(account)
    word_source_language = source_language or await LanguageModel.get(id=word.language_id)
    existing = await WordTranslateModel.get_or_none(
        word_id=word.id,
        language_id=target_language.id,
        account_id=account.id,
    )
    if existing is not None:
        return existing

    translate = await _translate_text(
        word.name,
        account,
        target_language,
        purpose="word",
        source_language=word_source_language,
    )
    word_type = "WRD" if _is_word_token(word.name) else "SYM"
    obj = await WordTranslateModel.create(
        word_id=word.id,
        language_id=target_language.id,
        account_id=account.id,
        translate=translate,
        transliteration=_fake_transliteration(word.name),
        word_type=word_type,
    )
    return obj


async def _serialize_word_translate(
    word_translate: WordTranslateModel,
    account: AccountModel,
) -> dict[str, Any]:
    word = await WordModel.get(id=word_translate.word_id)
    etymology = await CompatWordEtymologyModel.get_or_none(word_id=word.id)
    return {
        "id": word_translate.id,
        "type": word_translate.word_type or "WRD",
        "translate": word_translate.translate,
        "transliteration": word_translate.transliteration,
        "gender": word_translate.gender,
        "ai_word": bool(etymology),
        "word": await _serialize_word_model(word, account),
    }


async def _word_translates_for_links(
    links: list[CompatTextPartWordModel] | list[CompatPhraseWordModel],
    account: AccountModel,
    *,
    ensure_missing: bool = False,
) -> list[dict[str, Any]]:
    seen: set[int] = set()
    result: list[dict[str, Any]] = []
    target_language = await _target_language(account)
    for link in links:
        word_chapter = await WordChapterModel.get(id=link.word_chapter_id)
        word = await WordModel.get(id=word_chapter.word_id)
        if word.id in seen or not _is_word_token(word_chapter.name):
            continue
        seen.add(word.id)
        word_translate = await WordTranslateModel.get_or_none(
            word_id=word.id,
            language_id=target_language.id,
            account_id=account.id,
        )
        if word_translate is None and ensure_missing:
            source_language = await LanguageModel.get(id=word.language_id)
            word_translate = await _ensure_word_translate(
                word,
                account,
                target_language,
                source_language=source_language,
            )
        if word_translate is None:
            continue
        result.append(await _serialize_word_translate(word_translate, account))
    return result


async def _serialize_text_part(
    text_part: CompatTextPartModel,
    account: AccountModel,
) -> dict[str, Any]:
    links = await CompatTextPartWordModel.filter(text_part_id=text_part.id).order_by("position")
    return {
        "id": text_part.id,
        "name": text_part.name,
        "chapter": text_part.chapter_id,
        "chapter_id": text_part.chapter_id,
        "translate": (
            {
                "id": text_part.id,
                "translate": text_part.translate,
                "description": text_part.description,
            }
            if text_part.translate
            else None
        ),
        "transliteration": text_part.transliteration,
        "description": text_part.description,
        "ai_voice": (
            {"id": text_part.id, "file": _public_file_path(text_part.ai_voice_file)}
            if text_part.ai_voice_file
            else None
        ),
        "words": await _word_translates_for_links(links, account),
    }


async def _serialize_phrase(
    phrase: CompatPhraseModel,
    account: AccountModel,
) -> dict[str, Any]:
    links = await CompatPhraseWordModel.filter(phrase_id=phrase.id).order_by("position")
    return {
        "id": phrase.id,
        "name": phrase.name,
        "chapter": phrase.chapter_id,
        "chapter_id": phrase.chapter_id,
        "text_part": phrase.text_part_id,
        "text_part_id": phrase.text_part_id,
        "translate": (
            {
                "id": phrase.id,
                "translate": phrase.translate,
                "description": phrase.description,
            }
            if phrase.translate
            else None
        ),
        "transliteration": phrase.transliteration,
        "description": phrase.description,
        "ai_voice": (
            {"id": phrase.id, "file": _public_file_path(phrase.ai_voice_file)}
            if phrase.ai_voice_file
            else None
        ),
        "words": await _word_translates_for_links(links, account),
    }


async def _study_word_detail(word: WordModel, account: AccountModel) -> dict[str, Any]:
    source_language = await LanguageModel.get(id=word.language_id)
    word_translate = await _ensure_word_translate(
        word,
        account,
        source_language=source_language,
    )
    voice = await WordVoiceModel.get_or_none(word_id=word.id)
    return {
        "id": word.id,
        "name": word.name,
        "translate": await _serialize_word_translate(word_translate, account),
        "ai_voice": (
            {"id": voice.id, "file": _public_file_path(voice.file_path)}
            if voice
            else None
        ),
    }


async def _serialize_study_phrase(
    study: CompatStudyPhraseModel,
    account: AccountModel,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": study.id,
        "is_active": study.is_active,
        "chapter": study.chapter_id,
        "chapter_id": study.chapter_id,
        "audio_average": study.audio_average,
        "forward_average": study.forward_average,
        "reverse_average": study.reverse_average,
        "average": study.average,
        "success_logs": study.success_logs,
        "create_time": study.created_at.astimezone(timezone.utc).isoformat(),
    }
    if study.word_id:
        word = await WordModel.get(id=study.word_id)
        result["word"] = await _study_word_detail(word, account)
    if study.text_part_id:
        text_part = await CompatTextPartModel.get(id=study.text_part_id)
        result["text_part"] = await _serialize_text_part(text_part, account)
    if study.phrase_id:
        phrase = await CompatPhraseModel.get(id=study.phrase_id)
        result["phrase"] = await _serialize_phrase(phrase, account)
    return result


async def _assert_study_log_callback_owner(
    study: CompatStudyPhraseModel,
    callback_query: dict[str, Any],
) -> None:
    from_user = callback_query.get("from") or {}
    from_user_id = _safe_int(from_user.get("id"))
    if not from_user_id:
        return
    profile = await AuthProfileModel.get_or_none(
        account_id=study.account_id,
        provider_type=AuthProviderType.TELEGRAM,
    )
    if profile and profile.provider_id and profile.provider_id != str(from_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


async def _recalculate_study_phrase_scores(study: CompatStudyPhraseModel) -> None:
    logs = await CompatStudyPhraseLogModel.filter(
        study_phrase_id=study.id,
        rank__isnull=False,
    )
    ranked = [log for log in logs if log.rank is not None]
    study.success_logs = len(ranked)

    for study_type in STUDY_PHRASE_TYPES:
        type_ranks = [log.rank for log in ranked if log.study_type == study_type]
        setattr(
            study,
            f"{study_type}_average",
            (sum(type_ranks) / len(type_ranks)) if type_ranks else 0,
        )

    ranks = [log.rank for log in ranked]
    study.average = (sum(ranks) / len(ranks)) if ranks else 0
    await study.save()


async def _answer_telegram_callback_query(
    callback_query: dict[str, Any],
    text: str,
) -> None:
    if not settings.tg_bot_token:
        return
    callback_query_id = str(callback_query.get("id") or "")
    if not callback_query_id:
        return
    try:
        bot = Bot(token=settings.tg_bot_token)
        async with bot.session:
            await bot.answer_callback_query(
                callback_query_id=callback_query_id,
                text=text,
                show_alert=False,
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Telegram callback answer failed: %s", exc)


async def _rate_study_phrase_log(
    *,
    log_id: int,
    rank: int,
    callback_query: dict[str, Any],
) -> dict[str, Any]:
    if rank < 1 or rank > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rank must be between 1 and 5")

    log = await CompatStudyPhraseLogModel.get_or_none(id=log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    study = await CompatStudyPhraseModel.get(id=log.study_phrase_id)
    await _assert_study_log_callback_owner(study, callback_query)

    log.rank = rank
    await log.save()
    await _recalculate_study_phrase_scores(study)
    await _answer_telegram_callback_query(callback_query, f"Saved: {rank}")

    return {
        "success": True,
        "handled": "study_phrase_rating",
        "study_phrase_id": study.id,
        "log_id": log.id,
        "rank": rank,
        "study_type": log.study_type,
    }


def _study_web_app_url(study_id: int) -> str:
    base = (settings.web_app_url or "").rstrip("/") or "https://tg.lazy-reader.com"
    return f"{base}?study={study_id}"


async def _telegram_account_from_payload(payload: dict[str, Any]) -> AccountModel:
    callback_query = payload.get("callback_query") or {}
    message = payload.get("message") or {}
    source = callback_query.get("from") or message.get("from") or message.get("chat") or {}
    tg_user_id = _safe_int(source.get("id"))
    if not tg_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="telegram user id is required")
    profile = await AuthProfileModel.get_or_none(
        provider_type=AuthProviderType.TELEGRAM,
        provider_id=str(tg_user_id),
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    account = await AccountModel.get_or_none(id=profile.account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return account


def _telegram_user_id_from_payload(payload: dict[str, Any]) -> int:
    callback_query = payload.get("callback_query") or {}
    message = payload.get("message") or {}
    source = callback_query.get("from") or message.get("from") or message.get("chat") or {}
    tg_user_id = _safe_int(source.get("id"))
    if not tg_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="telegram user id is required")
    return tg_user_id


def _telegram_user_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    callback_query = payload.get("callback_query") or {}
    message = payload.get("message") or {}
    source = callback_query.get("from") or message.get("from") or message.get("chat") or {}
    tg_user_id = _safe_int(source.get("id"))
    if not tg_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="telegram user id is required")
    return {
        **source,
        "id": tg_user_id,
    }


def _compat_referral_code(account: AccountModel) -> str:
    return f"lr_{account.id}"


def _compat_referral_owner_id(referral_code: str) -> int:
    code = referral_code.strip()
    if code.startswith("ref_"):
        code = code[4:]
    for prefix in ("lr_", "lr-"):
        if code.startswith(prefix):
            return _safe_int(code[len(prefix) :])
    return 0


def _telegram_start_referral_code(payload: dict[str, Any]) -> str:
    message = payload.get("message") or {}
    text = _first_str(message.get("text")).strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return ""
    start_argument = parts[1].strip().split(maxsplit=1)[0]
    if not start_argument.startswith("ref_"):
        return ""
    return start_argument[4:]


def _telegram_web_app_root_url() -> str:
    base = (settings.web_app_url or "").strip() or "https://tg.lazy-reader.com"
    return f"{base.rstrip('/')}/"


def _telegram_start_keyboard() -> list[list[dict[str, str]]]:
    return [[{"text": "Open WebApp", "web_app": _telegram_web_app_root_url()}]]


def _telegram_web_app_url_for_path(path: Any) -> str:
    path_value = _first_str(path) or "/"
    if path_value.startswith(("http://", "https://")):
        return path_value
    if not path_value.startswith("/"):
        path_value = f"/{path_value}"
    return f"{_telegram_web_app_root_url().rstrip('/')}{path_value}"


def _telegram_web_app_keyboard(web_app_url: str) -> list[list[dict[str, str]]]:
    return [[{"text": "Open WebApp", "web_app": web_app_url}]]


async def _send_telegram_web_app_link(
    account: AccountModel,
    *,
    text: Any,
    path: Any,
) -> tuple[str, list[list[dict[str, str]]]]:
    profile = await _telegram_profile(account)
    if not profile or not profile.provider_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram profile is missing.")
    if not settings.tg_bot_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot token is not configured.",
        )

    web_app_url = _telegram_web_app_url_for_path(path)
    message_text = _first_str(text) or "Open Lazy Reader"
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open WebApp", web_app=WebAppInfo(url=web_app_url))]
        ]
    )

    try:
        bot = Bot(token=settings.tg_bot_token)
        async with bot.session:
            await bot.send_message(
                chat_id=int(profile.provider_id),
                text=message_text,
                reply_markup=reply_markup,
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Telegram link delivery failed: {exc}",
        ) from exc

    return web_app_url, _telegram_web_app_keyboard(web_app_url)


def _telegram_user_display_name(user: dict[str, Any]) -> str:
    name = " ".join(
        part
        for part in [
            _first_str(user.get("first_name")),
            _first_str(user.get("last_name")),
        ]
        if part
    ).strip()
    return name or _first_str(user.get("username")) or str(user["id"])


def _telegram_start_text(*, account: AccountModel, user: dict[str, Any], is_new: bool) -> str:
    display_name = account.public_name or _telegram_user_display_name(user)
    if is_new:
        text = (
            f"Welcome to Lazy Reader, {display_name}!\n\n"
            "Create books, translate text, listen to phrases, learn words, "
            "and explore etymology with AI."
        )
        if settings.credits_start_bonus > 0:
            text = (
                f"{text}\n\n"
                f"New users can claim {settings.credits_start_bonus}★ credits "
                "with /start_bonus."
            )
        return text
    return f"Hello, {display_name}!\n\nThank you for using Lazy Reader."


async def _get_or_create_telegram_account_from_update(
    payload: dict[str, Any],
) -> tuple[AccountModel, AuthProfileModel, bool]:
    user = _telegram_user_from_payload(payload)
    tg_user_id = str(user["id"])
    profile = await AuthProfileModel.get_or_none(
        provider_type=AuthProviderType.TELEGRAM,
        provider_id=tg_user_id,
    )
    if profile:
        account = await AccountModel.get(id=profile.account_id)
        profile.provider_data = {
            **(profile.provider_data or {}),
            "user": user,
        }
        profile.language_code = _first_str(user.get("language_code")) or profile.language_code
        await profile.save()
        return account, profile, False

    username_tail = _first_str(user.get("username")) or _first_str(user.get("first_name")) or tg_user_id
    username = _truncate(f"TG:{tg_user_id}:{username_tail}", 100)
    account = await AccountModel.create(
        username=username,
        public_name=_truncate(_telegram_user_display_name(user), 255),
        credits=0,
    )
    profile = await AuthProfileModel.create(
        account_id=account.id,
        provider_type=AuthProviderType.TELEGRAM,
        provider_id=tg_user_id,
        provider_data={"user": user},
        language_code=_first_str(user.get("language_code")) or settings.default_language,
    )
    return account, profile, True


async def _record_compat_referral(
    *,
    account: AccountModel,
    profile: AuthProfileModel,
    referral_code: str,
) -> bool:
    owner_id = _compat_referral_owner_id(referral_code)
    if not owner_id or owner_id == account.id:
        return False
    owner = await AccountModel.get_or_none(id=owner_id)
    if not owner:
        return False
    data = dict(profile.provider_data or {})
    existing_referral = data.get(REFERRAL_PROFILE_KEY)
    if isinstance(existing_referral, dict) and _safe_int(existing_referral.get("account_id")):
        return False
    data[REFERRAL_PROFILE_KEY] = {
        "account_id": owner.id,
        "code": _compat_referral_code(owner),
        "percentage": REFERRAL_PERCENTAGE,
        "create_time": datetime.now(timezone.utc).isoformat(),
    }
    profile.provider_data = data
    await profile.save()
    return True


async def _handle_start_from_telegram_update(payload: dict[str, Any]) -> dict[str, Any]:
    account, profile, is_new = await _get_or_create_telegram_account_from_update(payload)
    user = _telegram_user_from_payload(payload)
    referral_added = await _record_compat_referral(
        account=account,
        profile=profile,
        referral_code=_telegram_start_referral_code(payload),
    )
    return {
        "success": True,
        "handled": "start",
        "account_id": account.id,
        "is_new": is_new,
        "referral_added": referral_added,
        "text": _telegram_start_text(account=account, user=user, is_new=is_new),
        "web_app_url": _telegram_web_app_root_url(),
        "keyboard": _telegram_start_keyboard(),
    }


async def _assert_telegram_admin(account: AccountModel) -> None:
    role = await AccessRoleModel.get_or_none(account_id=account.id)
    if role and role.role == AccessRole.SUPERUSER:
        return
    if await _is_configured_telegram_admin(account):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="telegram admin is required")


def _configured_telegram_admin_ids() -> set[str]:
    raw = str(settings.telegram_admin_user_ids or "")
    return {
        item.strip()
        for item in re.split(r"[,;\s|]+", raw)
        if item.strip()
    }


async def _is_configured_telegram_admin(account: AccountModel) -> bool:
    admin_ids = _configured_telegram_admin_ids()
    if not admin_ids:
        return False
    profile = await AuthProfileModel.get_or_none(
        account_id=account.id,
        provider_type=AuthProviderType.TELEGRAM,
    )
    return bool(profile and profile.provider_id in admin_ids)


async def _telegram_admin_help_text(payload: dict[str, Any]) -> str:
    is_admin = False
    try:
        account = await _telegram_account_from_payload(payload)
        role = await AccessRoleModel.get_or_none(account_id=account.id)
        is_admin = bool(role and role.role == AccessRole.SUPERUSER) or await _is_configured_telegram_admin(account)
    except HTTPException:
        is_admin = False

    lines = [
        "Lazy Reader bot commands:",
        "/start - open the mini app",
        "/start_bonus - claim start bonus once",
        "/task - get a study task",
        "/reset_tasks - reset pending study tasks",
        "",
        "Admin credits:",
        "/bonus <account_id> <credits>",
        "/add <account_id> <credits>",
        "/credit <account_id> <credits>",
        "Example: /bonus 12 500",
        "",
        "Manual bill:",
        "credits:<account_id>:<credits>:<cost>:RUB",
        "Example: credits:12:500:500:RUB",
        "",
        "Admin stats:",
        "/users",
        "/stats",
    ]
    if not is_admin:
        lines.append("")
        lines.append("Admin commands require SUPERUSER or TELEGRAM_ADMIN_USER_IDS.")
    return "\n".join(lines)


async def _handle_telegram_help_from_update(payload: dict[str, Any]) -> dict[str, Any]:
    text = await _telegram_admin_help_text(payload)
    await _send_telegram_text_from_update(payload, text)
    return {"success": True, "handled": "help", "text": text}


async def _handle_unknown_telegram_command(
    payload: dict[str, Any],
    command: str,
) -> dict[str, Any]:
    text = "Unknown command. Use /help to see Lazy Reader bot commands."
    await _send_telegram_text_from_update(payload, text)
    return {"success": True, "handled": "unknown_command", "command": command, "text": text}


def _manual_bill_keyboard(bill_id: int) -> list[list[dict[str, str]]]:
    return [
        [
            {"text": "YES", "callback_data": f"manual_bill_{bill_id}_yes"},
            {"text": "NO", "callback_data": f"manual_bill_{bill_id}_no"},
        ]
    ]


def _manual_bill_currency(value: str | None) -> Currency:
    if not value:
        return Currency.RUB
    try:
        return Currency(value.upper())
    except ValueError:
        return Currency.RUB


def _admin_bonus_match(text: str) -> re.Match[str] | None:
    compact = text.strip()
    return ADMIN_BONUS_COMMAND_RE.match(compact) or ADMIN_BONUS_MESSAGE_RE.match(compact)


def _admin_bonus_credits(value: str) -> Decimal:
    try:
        credits = Decimal(value.replace(",", ".")).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid bonus credits amount",
        ) from exc
    if credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="bonus credits amount must be positive",
        )
    return credits


async def _create_admin_bonus_from_telegram_update(payload: dict[str, Any]) -> dict[str, Any]:
    admin = await _telegram_account_from_payload(payload)
    await _assert_telegram_admin(admin)

    message = payload.get("message") or {}
    text = str(message.get("text") or "")
    match = _admin_bonus_match(text)
    if not match:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid bonus message")

    target_account_id = _safe_int(match.group("account_id"))
    target = await AccountModel.get_or_none(id=target_account_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="target account not found")

    credits_amount = _admin_bonus_credits(match.group("credits"))
    transaction = await _create_transaction(target, TransactionType.MANUAL, credits_amount)
    message_text = (
        f"Bonus granted\n"
        f"User: {target.id} / {target.username}\n"
        f"Credits: {credits_amount}"
    )
    await _send_telegram_text_from_update(payload, message_text)
    return {
        "success": True,
        "handled": "admin_bonus_granted",
        "target_account_id": target.id,
        "credits_amount": float(credits_amount),
        "transaction_id": transaction.id,
        "text": message_text,
    }


async def _create_manual_bill_from_telegram_update(payload: dict[str, Any]) -> dict[str, Any]:
    admin = await _telegram_account_from_payload(payload)
    await _assert_telegram_admin(admin)

    message = payload.get("message") or {}
    text = str(message.get("text") or "")
    match = MANUAL_CREDITS_MESSAGE_RE.match(text)
    if not match:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid manual credits message")

    target_account_id = _safe_int(match.group("account_id"))
    target = await AccountModel.get_or_none(id=target_account_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="target account not found")

    credits_amount = Decimal(match.group("credits"))
    cost = _safe_int(match.group("cost"), 0)
    currency = _manual_bill_currency(match.group("currency"))
    bill = await BillModel.create(
        account_id=target.id,
        credits_amount=credits_amount,
        cost=cost,
        currency=currency,
        payment_service=PaymentService.MANUAL,
        payment_data={
            "admin": {"account_id": admin.id, "username": admin.username},
            "source": "telegram_update",
        },
    )

    return {
        "success": True,
        "handled": "manual_bill_created",
        "bill_id": bill.id,
        "target_account_id": target.id,
        "credits_amount": float(credits_amount),
        "cost": cost,
        "currency": currency.value,
        "text": f"User: {target.id} / {target.username}\nCredits: {credits_amount}\nCost: {cost}",
        "keyboard": _manual_bill_keyboard(bill.id),
    }


async def _handle_manual_bill_callback(
    *,
    payload: dict[str, Any],
    bill_id: int,
    answer: str,
) -> dict[str, Any]:
    admin = await _telegram_account_from_payload(payload)
    await _assert_telegram_admin(admin)

    bill = await BillModel.get_or_none(id=bill_id)
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="manual bill not found")

    if answer == "no":
        target_account_id = bill.account_id
        await BillModel.filter(id=bill.id).delete()
        return {
            "success": True,
            "handled": "manual_bill_deleted",
            "bill_id": bill_id,
            "target_account_id": target_account_id,
            "text": f"Manual bill {bill_id} deleted.",
        }

    tg_user_id = _telegram_user_id_from_payload(payload)
    result = await TelegramBot._base_payment_successful(
        bill_id=bill.id,
        transaction=f"telegram:{tg_user_id}:{bill.id}",
        payment_data={"admin": [admin.id, admin.username]},
    )
    return {
        "success": result.success,
        "handled": "manual_bill_confirmed",
        "bill_id": bill.id,
        "target_account_id": bill.account_id,
        "text": f"Manual bill {bill.id} confirmed for account {bill.account_id}.",
    }


async def _handle_start_bonus_from_telegram_update(payload: dict[str, Any]) -> dict[str, Any]:
    account = await _telegram_account_from_payload(payload)
    exists = await AccountTransactionModel.get_or_none(
        account_id=account.id,
        transaction_type=TransactionType.START_BONUS,
    )
    if exists:
        return {
            "success": False,
            "handled": "start_bonus",
            "credits_amount": 0.0,
            "message": "Start bonus already exists",
        }

    await _create_transaction(
        account,
        TransactionType.START_BONUS,
        Decimal(settings.credits_start_bonus),
    )
    return {
        "success": True,
        "handled": "start_bonus",
        "credits_amount": float(settings.credits_start_bonus),
        "message": "Start bonus granted",
    }


def _telegram_profile_user(profile: AuthProfileModel | None) -> dict[str, Any]:
    if not profile:
        return {}
    data = profile.provider_data or {}
    user = data.get("user") or data.get("auth_data", {}).get("user") or {}
    return user if isinstance(user, dict) else {}


def _telegram_user_line(
    *,
    account: AccountModel,
    profile: AuthProfileModel | None,
    books_count: int,
) -> str:
    user = _telegram_profile_user(profile)
    username = _first_str(user.get("username"))
    display_name = account.public_name or " ".join(
        part
        for part in [
            _first_str(user.get("first_name")),
            _first_str(user.get("last_name")),
        ]
        if part
    ).strip()
    tg_user_id = _first_str(user.get("id") or (profile.provider_id if profile else ""))
    handle = f"@{username}" if username else f"tg:{tg_user_id}" if tg_user_id else "-"
    name = _truncate(display_name or account.username, 28)
    credits = Decimal(str(account.credits or 0)).quantize(Decimal("0.01"))
    return f"#{account.id} | {handle} | {name} | ★{credits} | books={books_count}"


async def _recent_telegram_users_lines(limit: int = 30) -> list[str]:
    accounts = await AccountModel.all().order_by("-id").limit(limit)
    if not accounts:
        return []

    account_ids = [account.id for account in accounts]
    profiles = await AuthProfileModel.filter(
        account_id__in=account_ids,
        provider_type=AuthProviderType.TELEGRAM,
    )
    profiles_by_account = {profile.account_id: profile for profile in profiles}

    books = await BookModel.filter(account_id__in=account_ids).values("account_id")
    books_count_by_account: dict[int, int] = {}
    for item in books:
        account_id = _safe_int(item.get("account_id"))
        books_count_by_account[account_id] = books_count_by_account.get(account_id, 0) + 1

    return [
        _telegram_user_line(
            account=account,
            profile=profiles_by_account.get(account.id),
            books_count=books_count_by_account.get(account.id, 0),
        )
        for account in accounts
    ]


async def _handle_users_stats_from_telegram_update(payload: dict[str, Any]) -> dict[str, Any]:
    account = await _telegram_account_from_payload(payload)
    await _assert_telegram_admin(account)

    since = datetime.now(timezone.utc) - timedelta(days=15)
    totals = {
        "accounts": await AccountModel.filter(created_at__gte=since).count(),
        "books": await BookModel.filter(created_at__gte=since).count(),
    }
    text = (
        "<b>Date</b> | <b>accounts</b> | <b>books</b>\n"
        "--------------------------\n"
        f"<b>Total (15d):</b> accounts={totals['accounts']} books={totals['books']}"
    )
    user_lines = await _recent_telegram_users_lines()
    if user_lines:
        text = f"{text}\n\n<b>Recent users:</b>\n" + "\n".join(user_lines)
    return {
        "success": True,
        "handled": "users_stats",
        "totals": totals,
        "users": user_lines,
        "text": text,
    }


async def _handle_payment_stats_from_telegram_update(payload: dict[str, Any]) -> dict[str, Any]:
    account = await _telegram_account_from_payload(payload)
    await _assert_telegram_admin(account)

    since = datetime.now(timezone.utc) - timedelta(days=7)
    bills = await BillModel.filter(
        created_at__gte=since,
        payment_service=PaymentService.TG_STARS,
    ).all()
    paid_bills = [bill for bill in bills if bill.success_time is not None]
    profit = sum(int(bill.cost or 0) for bill in paid_bills)
    paid = len(paid_bills)
    total = len(bills)
    avg = int(profit / paid) if paid else 0
    summary = {
        "profit": profit,
        "avg": avg,
        "paid": paid,
        "total": total,
    }
    text = (
        f"{PaymentService.TG_STARS.value}\n"
        "<b>Summary:</b>\n"
        f"Profit: {profit}\n"
        f"Avg: {avg}\n"
        f"Paid: {paid}\n"
        f"Total: {total}"
    )
    return {
        "success": True,
        "handled": "payment_stats",
        "payment_service": PaymentService.TG_STARS.value,
        "summary": summary,
        "text": text,
    }


async def _handle_study_task_delete_callback(payload: dict[str, Any]) -> dict[str, Any]:
    await _telegram_account_from_payload(payload)
    callback_query = payload.get("callback_query") or {}
    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    return {
        "success": True,
        "handled": "study_task_deleted",
        "chat_id": _safe_int(chat.get("id")),
        "message_id": _safe_int(message.get("message_id")),
    }


async def _study_has_voice(study: CompatStudyPhraseModel) -> bool:
    if study.word_id and await WordVoiceModel.get_or_none(word_id=study.word_id):
        return True
    if study.text_part_id:
        text_part = await CompatTextPartModel.get_or_none(id=study.text_part_id)
        return bool(text_part and text_part.ai_voice_file)
    if study.phrase_id:
        phrase = await CompatPhraseModel.get_or_none(id=study.phrase_id)
        return bool(phrase and phrase.ai_voice_file)
    return False


async def _resolve_study_task_type(
    study: CompatStudyPhraseModel,
    requested_type: str | None,
) -> str:
    if requested_type:
        return requested_type
    if await _study_has_voice(study) and study.success_logs % 3 == 0:
        return "audio"
    return "forward" if study.success_logs % 2 == 0 else "reverse"


async def _study_task_parts(study: CompatStudyPhraseModel, account: AccountModel) -> tuple[str, str, str]:
    if study.word_id:
        word = await WordModel.get(id=study.word_id)
        word_translate = await _ensure_word_translate(word, account)
        return word.name.lower(), word_translate.translate or "", getattr(word_translate, "description", "") or ""
    if study.text_part_id:
        text_part = await CompatTextPartModel.get(id=study.text_part_id)
        return text_part.name.lower(), text_part.translate or "", text_part.description or ""
    if study.phrase_id:
        phrase = await CompatPhraseModel.get(id=study.phrase_id)
        return phrase.name.lower(), phrase.translate or "", phrase.description or ""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


def _study_task_text(study_type: str, text: str, translation: str, description: str) -> str:
    if study_type == "reverse":
        return f"{translation} \n\n || {text}  \n\n {description}||"
    if study_type == "audio":
        return f"|| {text}  \n\n {translation} \n\n {description}||"
    return f"{text} \n || {translation} \n {description}||"


def _study_task_keyboard(log_id: int, study_id: int) -> list[list[dict[str, str]]]:
    keyboard: list[list[dict[str, str]]] = [
        [
            {"text": str(rank), "callback_data": f"study_phrase_{log_id}_{rank}"}
            for rank in range(1, 6)
        ],
    ]
    keyboard.append([{"text": "Open WebApp", "web_app": _study_web_app_url(study_id)}])
    return keyboard


def _telegram_chat_id_from_payload(payload: dict[str, Any]) -> int:
    callback_query = payload.get("callback_query") or {}
    message = payload.get("message") or callback_query.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = _safe_int(chat.get("id"))
    if chat_id:
        return chat_id
    source = callback_query.get("from") or message.get("from") or {}
    return _safe_int(source.get("id"))


def _inline_keyboard_from_payload(
    keyboard: list[list[dict[str, Any]]],
) -> InlineKeyboardMarkup | None:
    rows: list[list[InlineKeyboardButton]] = []
    for row in keyboard:
        buttons: list[InlineKeyboardButton] = []
        for item in row:
            text = str(item.get("text") or "")
            if not text:
                continue
            web_app = item.get("web_app")
            if isinstance(web_app, str):
                buttons.append(InlineKeyboardButton(text=text, web_app=WebAppInfo(url=web_app)))
                continue
            buttons.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=str(item.get("callback_data") or ""),
                )
            )
        if buttons:
            rows.append(buttons)
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


async def _send_telegram_text_from_update(
    payload: dict[str, Any],
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    if not settings.tg_bot_token:
        return
    chat_id = _telegram_chat_id_from_payload(payload)
    if not chat_id or not text.strip():
        return
    try:
        bot = Bot(token=settings.tg_bot_token)
        async with bot.session:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Telegram message delivery failed: %s", exc)


async def _send_telegram_result_from_update(
    payload: dict[str, Any],
    result: dict[str, Any],
) -> None:
    text = str(result.get("text") or result.get("message") or "")
    reply_markup = _inline_keyboard_from_payload(result.get("keyboard") or [])
    parse_mode = "HTML" if "<b>" in text else None
    await _send_telegram_text_from_update(payload, text, reply_markup, parse_mode)


async def _send_study_task_message_from_update(
    payload: dict[str, Any],
    result: dict[str, Any],
) -> None:
    handled = result.get("handled")
    if handled == "study_task_created":
        text = str(result.get("text") or "")
        reply_markup = _inline_keyboard_from_payload(result.get("keyboard") or [])
    elif handled == "study_task_missing":
        text = "No active study items yet. Add a word or phrase to study in the mini app."
        reply_markup = None
    else:
        return
    await _send_telegram_text_from_update(payload, text, reply_markup)


async def _create_study_task_for_account(
    *,
    account: AccountModel,
    requested_type: str | None,
) -> dict[str, Any]:
    candidates = await CompatStudyPhraseModel.filter(
        account_id=account.id,
        is_active=True,
    ).order_by("average", "id")
    if requested_type == "audio":
        candidates = [study for study in candidates if await _study_has_voice(study)]
    if not candidates:
        return {"success": False, "handled": "study_task_missing"}

    study = candidates[0]
    study_type = await _resolve_study_task_type(study, requested_type)
    text, translation, description = await _study_task_parts(study, account)
    log = await CompatStudyPhraseLogModel.create(
        study_phrase_id=study.id,
        study_type=study_type,
        is_active=True,
    )
    return {
        "success": True,
        "handled": "study_task_created",
        "study_phrase_id": study.id,
        "log_id": log.id,
        "study_type": study_type,
        "text": _study_task_text(study_type, text, translation, description),
        "keyboard": _study_task_keyboard(log.id, study.id),
        "web_app_url": _study_web_app_url(study.id),
    }


async def _create_study_task_from_telegram_update(
    *,
    payload: dict[str, Any],
    requested_type: str | None,
) -> dict[str, Any]:
    if requested_type is not None and requested_type not in STUDY_PHRASE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported study task type")
    account = await _telegram_account_from_payload(payload)
    result = await _create_study_task_for_account(account=account, requested_type=requested_type)
    await _send_study_task_message_from_update(payload, result)
    return result


async def _reset_study_tasks_from_telegram_update(payload: dict[str, Any]) -> dict[str, Any]:
    account = await _telegram_account_from_payload(payload)
    study_ids = await CompatStudyPhraseModel.filter(account_id=account.id).values_list("id", flat=True)
    query = CompatStudyPhraseLogModel.filter(
        study_phrase_id__in=study_ids,
        rank__isnull=True,
    )
    count = await query.count()
    await query.delete()
    return {"success": True, "handled": "study_tasks_reset", "count": count}


async def _chapter_percent(chapter: ChapterModel, account: AccountModel) -> int:
    progress = await CompatChapterProgressModel.get_or_none(
        account_id=account.id,
        chapter_id=chapter.id,
    )
    return progress.percent if progress else 0


async def _serialize_chapter(
    chapter: ChapterModel,
    account: AccountModel,
    with_content: bool = False,
) -> dict[str, Any]:
    source_url = chapter.source_url or ""
    result: dict[str, Any] = {
        "id": chapter.id,
        "name": chapter.name,
        "book": chapter.book_id,
        "book_id": chapter.book_id,
        "position": chapter.position,
        "is_ready": chapter.is_ready,
        "source_url": source_url,
        "input_url": source_url,
        "percent": await _chapter_percent(chapter, account),
    }
    if with_content:
        book = await BookModel.get(id=chapter.book_id)
        result["book"] = await _serialize_book(book, account, with_chapters=False)
        result["content"] = await _chapter_content(chapter, account)
    return result


async def _serialize_book(
    book: BookModel,
    account: AccountModel,
    with_chapters: bool = False,
) -> dict[str, Any]:
    chapters = await ChapterModel.filter(book_id=book.id, account_id=account.id).order_by("position", "id")
    chapters_data = [await _serialize_chapter(chapter, account) for chapter in chapters]
    ready_count = len([chapter for chapter in chapters if chapter.is_ready])
    ready_percent = round(ready_count * 100 / len(chapters), 2) if chapters else 100
    image = str(book.image) if getattr(book, "image", None) else ""
    result: dict[str, Any] = {
        "id": book.id,
        "name": book.name,
        "description": await _book_description(book, account),
        "language": book.language_id,
        "language_id": book.language_id,
        "chapters_count": len(chapters),
        "image": image or _placeholder_image_path(),
        "croped_image": image or _placeholder_image_path(),
        "file": None,
        "is_active": await _book_is_active(book, account),
        "is_book_ready": ready_count == len(chapters),
        "ready_percent": ready_percent,
    }
    result["chapters"] = chapters_data if with_chapters else [chapter.id for chapter in chapters]
    return result


async def _chapter_content(chapter: ChapterModel, account: AccountModel) -> list[dict[str, Any]]:
    word_chapters = await WordChapterModel.filter(chapter_id=chapter.id).order_by("position", "id")
    ids = [word_chapter.id for word_chapter in word_chapters]
    text_links = await CompatTextPartWordModel.filter(word_chapter_id__in=ids)
    phrase_links = await CompatPhraseWordModel.filter(word_chapter_id__in=ids)
    text_by_word = {link.word_chapter_id: link.text_part_id for link in text_links}
    phrase_by_word = {link.word_chapter_id: link.phrase_id for link in phrase_links}
    result = []
    for word_chapter in word_chapters:
        item = {
            "id": word_chapter.id,
            "name": word_chapter.name,
            "position": word_chapter.position,
            "p": word_chapter.position,
            "n": word_chapter.n,
        }
        if text_by_word.get(word_chapter.id):
            item["t"] = text_by_word[word_chapter.id]
        if phrase_by_word.get(word_chapter.id):
            item["h"] = phrase_by_word[word_chapter.id]
        if _is_word_token(word_chapter.name):
            item["w"] = word_chapter.word_id
        result.append(item)
    return result


async def _tokenize_chapter(chapter: ChapterModel, text: str) -> None:
    await WordChapterModel.filter(chapter_id=chapter.id).delete()
    language = await _word_language_from_chapter(chapter)
    position = 0
    lines = text.splitlines() or [text]
    for line_index, line in enumerate(lines):
        tokens = TOKEN_RE.findall(line)
        for token_index, token in enumerate(tokens):
            if not token.strip():
                continue
            name = _truncate(token, 255)
            word_name = _truncate(token.lower(), 100)
            word, _ = await WordModel.get_or_create(
                name=word_name,
                language_id=language.id,
            )
            n = 1 if token_index == len(tokens) - 1 and line_index < len(lines) - 1 else 0
            await WordChapterModel.create(
                name=name,
                word_id=word.id,
                chapter_id=chapter.id,
                position=position,
                n=n,
            )
            position += 1
    chapter.is_ready = True
    await chapter.save()


async def _create_chapter(
    *,
    book: BookModel,
    account: AccountModel,
    name: str,
    text: str,
    source_url: str = "",
) -> ChapterModel:
    position = await ChapterModel.filter(book_id=book.id).count()
    chapter = await ChapterModel.create(
        name=_truncate(name or f"Chapter {position + 1}", 255),
        book_id=book.id,
        account_id=account.id,
        source_url=_truncate(source_url, 500),
        position=position,
        is_ready=False,
    )
    book.chapters_count = await ChapterModel.filter(book_id=book.id).count()
    await book.save()
    if settings.event_broker_type == EventBrokerTypes.MOCK:
        register_chapter_brokers(EventBrokerTypes.MOCK)
    await DIPublisher.publish(
        payload=ChapterCreateRequestedEvent(
            book_id=book.id,
            chapter_id=chapter.id,
            text=text,
            pid=f"compat:chapter:{chapter.id}",
        ),
        group_id=f"book:{book.id}",
    )
    return chapter


async def _selected_word_chapters(
    indexes: list[int],
    account: AccountModel,
) -> list[WordChapterModel]:
    if not indexes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="indexes are required")
    items = await WordChapterModel.filter(id__in=indexes).order_by("position")
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="selected words not found")
    chapter_ids = {item.chapter_id for item in items}
    if len(chapter_ids) != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="selection must stay in one chapter")
    chapter = await ChapterModel.get(id=items[0].chapter_id)
    if chapter.account_id != account.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return items


async def _find_exact_text_part_for_word_chapters(
    items: list[WordChapterModel],
    account: AccountModel,
) -> CompatTextPartModel | None:
    selected_ids = list(dict.fromkeys(item.id for item in items))
    links = await CompatTextPartWordModel.filter(word_chapter_id__in=selected_ids)
    if not links:
        return None

    matches_by_text_part: dict[int, set[int]] = {}
    for link in links:
        matches_by_text_part.setdefault(link.text_part_id, set()).add(link.word_chapter_id)

    candidate_ids = [
        text_part_id
        for text_part_id, matched_ids in matches_by_text_part.items()
        if len(matched_ids) == len(selected_ids)
    ]
    if not candidate_ids:
        return None

    text_parts = await CompatTextPartModel.filter(
        id__in=candidate_ids,
        account_id=account.id,
        chapter_id=items[0].chapter_id,
    )
    if not text_parts:
        return None

    total_links = await CompatTextPartWordModel.filter(
        text_part_id__in=[text_part.id for text_part in text_parts],
    )
    sizes_by_text_part: dict[int, int] = {}
    for link in total_links:
        sizes_by_text_part[link.text_part_id] = sizes_by_text_part.get(link.text_part_id, 0) + 1

    exact = [
        text_part
        for text_part in text_parts
        if sizes_by_text_part.get(text_part.id, 0) == len(selected_ids)
    ]
    if not exact:
        return None
    return max(exact, key=lambda text_part: text_part.id)


async def _text_part_links(text_part: CompatTextPartModel) -> list[CompatTextPartWordModel]:
    return await CompatTextPartWordModel.filter(text_part_id=text_part.id).order_by("position")


async def _apply_text_part_translate_action(
    *,
    text_part: CompatTextPartModel,
    account: AccountModel,
    source_language: LanguageModel,
    target_language: LanguageModel,
    translate_type: str,
) -> None:
    links = await _text_part_links(text_part)
    if _translate_type_needs_words(translate_type):
        translated_text = await _ensure_word_translates_for_selected_links(
            links=links,
            account=account,
            source_language=source_language,
            target_language=target_language,
            text=text_part.name,
            translate_type=translate_type,
        )
        if translated_text and _translate_type_needs_text(translate_type):
            text_part.translate = _truncate(translated_text, 2048)
            await text_part.save()

    if _translate_type_needs_text(translate_type) and not text_part.translate:
        text_part.translate = await _translate_text(
            text_part.name,
            account,
            target_language,
            purpose=TEXT_TRANSLATE_TYPE,
            source_language=source_language,
        )
        await text_part.save()


async def _create_text_part_from_word_chapters(
    items: list[WordChapterModel],
    account: AccountModel,
    action: str | None = None,
    translate_type_value: Any = None,
) -> CompatTextPartModel:
    chapter = await ChapterModel.get(id=items[0].chapter_id)
    source_language = await _word_language_from_chapter(chapter)
    target_language = await _target_language(account)
    name = _join_tokens([item.name for item in items])
    text_part = await _find_exact_text_part_for_word_chapters(items, account)
    if text_part is None:
        text_part = await CompatTextPartModel.create(
            account_id=account.id,
            chapter_id=chapter.id,
            language_id=source_language.id,
            name=name,
            transliteration=_fake_transliteration(name),
        )
        for position, item in enumerate(items):
            await CompatTextPartWordModel.create(
                text_part_id=text_part.id,
                word_chapter_id=item.id,
                position=position,
            )
    elif text_part.language_id != source_language.id:
        text_part.language_id = source_language.id
        await text_part.save()

    action_value = str(action or "").lower()
    if action_value == "translate":
        await _apply_text_part_translate_action(
            text_part=text_part,
            account=account,
            source_language=source_language,
            target_language=target_language,
            translate_type=_compat_translate_type(translate_type_value),
        )
    if action_value == "create_voice":
        voice_result = await _voice_file_result(
            "text_part",
            text_part.id,
            text_part.name,
            account,
            source_language,
        )
        if voice_result.billable:
            text_part.ai_voice_file = voice_result.file_path
            await text_part.save()
    return text_part


async def _publish_segment_event_for_text_part(
    *,
    indexes: list[int],
    payload: dict[str, Any],
    account: AccountModel,
) -> None:
    action = _segment_action(payload.get("action"))
    create_dto = CreateSegmentByWordChapterIndexesDTO(
        indexes=indexes,
        a=action,
        translate_type=_segment_translate_type(payload.get("translate_type")),
    )
    await publish_segment_create_request_event(
        create_dto=create_dto,
        account=_account_entity(account),
        ai_model_entity=_local_ai_model(action),
    )


async def _create_phrase_from_word_chapters(
    items: list[WordChapterModel],
    account: AccountModel,
    action: str | None = None,
) -> CompatPhraseModel:
    chapter = await ChapterModel.get(id=items[0].chapter_id)
    source_language = await _word_language_from_chapter(chapter)
    target_language = await _target_language(account)
    name = _join_tokens([item.name for item in items])
    text_part_id = await _infer_text_part_id_for_phrase(items, account)
    phrase = await CompatPhraseModel.filter(
        account_id=account.id,
        chapter_id=chapter.id,
        language_id=source_language.id,
        text_part_id=text_part_id,
        name=name,
    ).order_by("-id").first()
    if phrase is None:
        phrase = await CompatPhraseModel.create(
            account_id=account.id,
            chapter_id=chapter.id,
            language_id=source_language.id,
            text_part_id=text_part_id,
            name=name,
            transliteration=_fake_transliteration(name),
        )
        for position, item in enumerate(items):
            await CompatPhraseWordModel.create(
                phrase_id=phrase.id,
                word_chapter_id=item.id,
                position=position,
            )

    action_value = str(action or "").lower()
    if action_value == "translate" and not phrase.translate:
        phrase.translate = await _translate_text(
            phrase.name,
            account,
            target_language,
            purpose="phrase",
            source_language=source_language,
        )
        phrase.description = phrase.description or f"Phrase explanation for: {name}"
        await phrase.save()
    if action_value == "create_voice" and not phrase.ai_voice_file:
        voice_result = await _voice_file_result(
            "phrase",
            phrase.id,
            phrase.name,
            account,
            source_language,
        )
        if voice_result.billable:
            phrase.ai_voice_file = voice_result.file_path
            await phrase.save()
    return phrase


async def _infer_text_part_id_for_phrase(
    items: list[WordChapterModel],
    account: AccountModel,
) -> int | None:
    selected_ids = list(dict.fromkeys(item.id for item in items))
    if not selected_ids:
        return None
    links = await CompatTextPartWordModel.filter(word_chapter_id__in=selected_ids)
    if not links:
        return None

    matches_by_text_part: dict[int, set[int]] = {}
    for link in links:
        matches_by_text_part.setdefault(link.text_part_id, set()).add(link.word_chapter_id)

    candidate_ids = [
        text_part_id
        for text_part_id, matched_word_ids in matches_by_text_part.items()
        if len(matched_word_ids) == len(selected_ids)
    ]
    if not candidate_ids:
        return None

    text_parts = await CompatTextPartModel.filter(
        id__in=candidate_ids,
        account_id=account.id,
        chapter_id=items[0].chapter_id,
    )
    if not text_parts:
        return None

    total_links = await CompatTextPartWordModel.filter(
        text_part_id__in=[text_part.id for text_part in text_parts],
    )
    sizes_by_text_part: dict[int, int] = {}
    for link in total_links:
        sizes_by_text_part[link.text_part_id] = sizes_by_text_part.get(link.text_part_id, 0) + 1

    best_match = min(
        text_parts,
        key=lambda text_part: (sizes_by_text_part.get(text_part.id, 0), -text_part.id),
    )
    return best_match.id


async def _get_word_translate_or_404(
    word_translate_id: int,
    account: AccountModel,
    *,
    ensure_missing: bool = True,
    required_ai_credits: Decimal = Decimal("0"),
) -> WordTranslateModel:
    word_translate = await WordTranslateModel.get_or_none(
        id=word_translate_id,
        account_id=account.id,
    )
    if word_translate:
        return word_translate
    word = await WordModel.get_or_none(id=word_translate_id)
    if word:
        target_language = await _target_language(account)
        existing = await WordTranslateModel.get_or_none(
            word_id=word.id,
            language_id=target_language.id,
            account_id=account.id,
        )
        if existing:
            return existing
        if not ensure_missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if required_ai_credits > 0:
            await _assert_ai_credits(account, required_ai_credits)
        return await _ensure_word_translate(word, account, target_language)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


async def _ensure_etymology(word: WordModel, account: AccountModel) -> CompatWordEtymologyModel:
    etymology = await CompatWordEtymologyModel.get_or_none(word_id=word.id)
    if etymology:
        return etymology
    target_language = await _target_language(account)
    source_language = await LanguageModel.get(id=word.language_id)
    provider = await _reader_ai_provider_for_account(account)
    explanation = await provider.explain_word(
        ReaderWordExplanationRequest(
            account_id=account.id,
            word_id=word.id,
            word=word.name,
            source_language_code=source_language.code,
            target_language_code=target_language.code,
        )
    )
    etymology = await CompatWordEtymologyModel.create(
        word_id=word.id,
        description=explanation.description,
        root_name=explanation.root_name,
        root_description=explanation.root_description,
    )
    parts = explanation.parts or (
        {
            "type": "root",
            "name": explanation.root_name,
            "description": explanation.root_description,
        },
    )
    for part in parts:
        await CompatWordPartModel.create(
            etymology_id=etymology.id,
            part_type=part.get("type") or "root",
            name=part.get("name") or explanation.root_name,
            description=part.get("description") or explanation.root_description,
        )
    return etymology


async def _create_transaction(
    account: AccountModel,
    transaction_type: TransactionType,
    value: Decimal,
    bill: BillModel | None = None,
) -> AccountTransactionModel:
    transaction = await AccountTransactionModel.create(
        account_id=account.id,
        transaction_type=transaction_type,
        credits_amount=value,
        bill_id=bill.id if bill else None,
    )
    account.credits = float(Decimal(str(account.credits or 0)) + value)
    await account.save()
    return transaction


async def _send_telegram_stars_invoice(
    account: AccountModel,
    bill: BillModel,
    cost: int,
) -> tuple[bool, str | None]:
    profile = await _telegram_profile(account)
    if not profile or not profile.provider_id:
        return False, "Telegram profile is missing."
    if not settings.tg_bot_token:
        return False, "Telegram bot token is not configured."
    try:
        bot = Bot(token=settings.tg_bot_token)
        async with bot.session:
            await bot.send_invoice(
                chat_id=int(profile.provider_id),
                title="Purchase Credits",
                description="Purchase Credits to use AI in Lazy Reader.",
                payload=str(bill.id),
                provider_token=settings.tg_payment_provider_token,
                currency=Currency.STAR.value,
                prices=[LabeledPrice(label=f"Credits: {cost}", amount=cost)],
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
            )
    except Exception as exc:
        return False, str(exc)
    return True, None


async def _serialize_transaction(transaction: AccountTransactionModel) -> dict[str, Any]:
    return {
        "id": transaction.id,
        "transaction_type": transaction.transaction_type,
        "bill_id": transaction.bill_id,
        "usage_id": transaction.usage_id,
        "credits_amount": str(transaction.credits_amount),
        "value": float(transaction.credits_amount),
        "create_time": transaction.created_at.astimezone(timezone.utc).isoformat(),
        "created_at": transaction.created_at.astimezone(timezone.utc).isoformat(),
    }


@router.options("/{rest_of_path:path}")
async def legacy_options(rest_of_path: str) -> dict[str, Any]:
    resource = rest_of_path.strip("/").split("/", 1)[0]
    actions = LEGACY_ACTIONS.get(resource, DEFAULT_LEGACY_ACTIONS)
    return {"name": resource, "actions": actions}


@router.post("/account/telegram_auth/")
async def telegram_auth(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    await _ensure_languages()
    auth_data = payload.get("auth_data") or payload.get("init_data_unsafe") or {}
    user = auth_data.get("user") or {}
    tg_user_id = _first_str(user.get("id") or auth_data.get("id"))
    if not tg_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram user is required")
    profile = await AuthProfileModel.get_or_none(
        provider_type=AuthProviderType.TELEGRAM,
        provider_id=tg_user_id,
    )
    if profile:
        account = await AccountModel.get(id=profile.account_id)
    else:
        username_tail = user.get("username") or user.get("first_name") or tg_user_id
        username = _truncate(f"TG:{tg_user_id}:{username_tail}", 100)
        full_name = " ".join(part for part in [user.get("first_name"), user.get("last_name")] if part)
        account = await AccountModel.create(
            username=username,
            public_name=_truncate(full_name, 255) or username,
            credits=0,
        )
        profile = await AuthProfileModel.create(
            account_id=account.id,
            provider_type=AuthProviderType.TELEGRAM,
            provider_id=tg_user_id,
            provider_data=auth_data,
            language_code=user.get("language_code") or settings.default_language,
        )
    profile.provider_data = {**(profile.provider_data or {}), **auth_data}
    profile.language_code = user.get("language_code") or profile.language_code
    await profile.save()
    token = generate_token(account.id, expires_delta=timedelta(days=365))
    return {"token": token, "account": await _serialize_account(account)}


@router.get("/account/load/")
async def load_account(account: AccountModel = Depends(_current_account)) -> dict[str, Any]:
    return await _serialize_account(account)


@router.get("/account/profile/")
async def get_account_profile(account: AccountModel = Depends(_current_account)) -> dict[str, Any]:
    return await _serialize_account(account)


@router.patch("/account/profile/")
async def update_account_profile(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    profile = await _telegram_profile(account)
    if not profile:
        profile = await AuthProfileModel.create(
            account_id=account.id,
            provider_type=AuthProviderType.TELEGRAM,
            provider_id=f"local:{account.id}",
            provider_data={},
            language_code=settings.default_language,
        )
    data = profile.provider_data or {}
    if payload.get("language_id"):
        language = await LanguageModel.get_or_none(id=_safe_int(payload.get("language_id")))
        if language:
            profile.language_code = language.code
            data["language_id"] = language.id
    for key in ("ai_type", "use_google_translate"):
        if key in payload:
            data[key] = payload[key]
    if payload.get("public_name"):
        account.public_name = _truncate(str(payload["public_name"]), 255)
        await account.save()
    profile.provider_data = data
    await profile.save()
    return await _serialize_account(account)


@router.post("/account/send_link_to_tg/")
async def send_link_to_tg(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    dry_run = _truthy(payload.get("dry_run"), False)
    if dry_run:
        web_app_url = _telegram_web_app_url_for_path(payload.get("path"))
        return {
            "detail": "Link sent successfully",
            "success": True,
            "dry_run": True,
            "web_app_url": web_app_url,
            "keyboard": _telegram_web_app_keyboard(web_app_url),
        }

    web_app_url, keyboard = await _send_telegram_web_app_link(
        account,
        text=payload.get("text"),
        path=payload.get("path"),
    )
    return {
        "detail": "Link sent successfully",
        "success": True,
        "web_app_url": web_app_url,
        "keyboard": keyboard,
    }


@router.get("/language/")
async def list_languages() -> list[dict[str, Any]]:
    await _ensure_languages()
    languages = await LanguageModel.all().order_by("ordering", "id")
    return [await _serialize_language(language) for language in languages]


@router.patch("/language/update_image_group/")
async def update_language_image_group(
    payload: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    # The legacy frontend keeps this hook for old visual language groups.
    # The DDD MVP has no language image persistence yet, so echo a stable payload.
    return {"id": payload.get("id"), "image_group": payload, "updated": True}


@router.get("/language/{language_id:int}/")
async def get_language(language_id: int) -> dict[str, Any]:
    language = await LanguageModel.get_or_none(id=language_id)
    if not language:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await _serialize_language(language)


@router.get("/book/load_cfg/")
async def load_book_cfg() -> dict[str, Any]:
    return {
        "stars_credits": 1,
        "credits_referral_percentage": 15,
        "language_levels": {
            "a1": "A1",
            "a2": "A2",
            "b1": "B1",
            "b2": "B2",
            "c1": "C1",
        },
        "ai_chapter_types": {
            "story": "Story",
            "dialog": "Dialog",
            "essay": "Essay",
        },
        "ai_types": [
            {"id": "local", "name": "Local"},
            {"id": "openai", "name": "OpenAI"},
            {"id": "deepseek", "name": "DeepSeek"},
        ],
        "transaction_types": [
            [TransactionType.START_BONUS.value, "Start bonus"],
            [TransactionType.PAYMENT.value, "Payment"],
            [TransactionType.AI_USAGE.value, "AI usage"],
            [TransactionType.REFERRAL.value, "Referral"],
            [TransactionType.MANUAL.value, "Manual"],
        ],
    }


@router.get("/book/")
async def list_books(
    page: int | None = Query(default=None),
    search: str | None = Query(default=None),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    query = BookModel.filter(account_id=account.id).order_by("-id")
    if search:
        query = query.filter(name__icontains=search)
    books = await query
    data = _paginate_sequence(await _filter_books_by_active(books, account, True), page)
    return {
        "count": data["count"],
        "results": [await _serialize_book(book, account) for book in data["results"]],
    }


@router.get("/book/archive/")
async def list_book_archive(
    account: AccountModel = Depends(_current_account),
) -> list[dict[str, Any]]:
    books = await BookModel.filter(account_id=account.id).order_by("-id")
    return [await _serialize_book(book, account) for book in books]


@router.post("/book/")
async def create_book(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    await _ensure_languages()
    language_id = _safe_int(payload.get("language_id") or payload.get("language"))
    language = await LanguageModel.get_or_none(id=language_id) or await _target_language(account)
    book = await BookModel.create(
        name=_truncate(str(payload.get("name") or "Untitled book"), 255),
        language_id=language.id,
        account_id=account.id,
        chapters_count=0,
        image=_image_path_from_payload(payload),
    )
    if "description" in payload:
        await _set_book_description(book, account, _first_str(payload.get("description")))
    return await _serialize_book(book, account, with_chapters=True)


@router.post("/book/generate/")
async def generate_book(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    language_id = _safe_int(payload.get("language_id") or payload.get("language"))
    language = await LanguageModel.get_or_none(id=language_id) or await _target_language(account)
    description = str(payload.get("description") or "Generated reading practice")
    language_level = str(payload.get("language_level") or payload.get("level") or "a1")
    chapter_type = str(payload.get("chapter_type") or payload.get("type") or "story")
    await _assert_ai_credits(account, Decimal("10"))
    title, text = await _generate_reader_chapter_material(
        account=account,
        language=language,
        description=description,
        language_level=language_level,
        chapter_type=chapter_type,
        purpose="book_generation",
        fallback_title="Generated book",
    )
    book = await BookModel.create(
        name=title,
        language_id=language.id,
        account_id=account.id,
        chapters_count=0,
        image="",
    )
    await _set_book_description(book, account, description)
    await _create_chapter(book=book, account=account, name=title, text=text)
    await _charge_compat_usage(
        account=account,
        usage_type=AccountUsageType.AI_BOOK,
        usage_id=book.id,
        credits_amount=Decimal("10"),
    )
    books = await BookModel.filter(account_id=account.id).order_by("-id")
    return {
        "count": len(books),
        "results": [await _serialize_book(item, account) for item in books],
    }


@router.post("/book/generate_chapters/")
async def generate_chapters(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    book_id = _safe_int(payload.get("book_id") or payload.get("book"))
    book = await BookModel.get_or_none(id=book_id, account_id=account.id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    description = str(payload.get("description") or "Generated chapter")
    language = await _book_language(book)
    language_level = str(payload.get("language_level") or payload.get("level") or "a1")
    chapter_type = str(payload.get("chapter_type") or payload.get("type") or "story")
    book_description = await _book_description(book, account)
    if not book_description:
        book_description = str(payload.get("book_description") or payload.get("bookDescription") or "")
    existing_chapters = await ChapterModel.filter(book_id=book.id).order_by("position", "id")
    await _assert_ai_credits(account, Decimal("6"))
    chapter_name, text = await _generate_reader_chapter_material(
        account=account,
        language=language,
        description=description,
        language_level=language_level,
        chapter_type=chapter_type,
        purpose="chapter_generation",
        fallback_title=f"Chapter {book.chapters_count + 1}",
        book_title=book.name,
        book_description=book_description,
        existing_chapter_titles=[chapter.name for chapter in existing_chapters],
    )
    chapter = await _create_chapter(book=book, account=account, name=chapter_name, text=text)
    await _charge_compat_usage(
        account=account,
        usage_type=AccountUsageType.AI_BOOK,
        usage_id=chapter.id,
        credits_amount=Decimal("6"),
    )
    return await _serialize_book(book, account, with_chapters=True)


@router.post("/book/generate_image/")
async def generate_book_image(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, str]:
    name = str(payload.get("name") or "")
    description = str(payload.get("description") or "")
    usage_seed = f"{name}\n{description}".encode("utf-8")
    usage_id = int(hashlib.sha256(usage_seed).hexdigest()[:8], 16) % 2_147_483_647
    await _assert_ai_credits(account, Decimal("4"))
    provider = await _reader_ai_provider_for_account(account)
    response = await provider.generate_image(
        ReaderImageRequest(
            account_id=account.id,
            name=name,
            description=description,
            fallback_source=PLACEHOLDER_PNG_DATA_URL,
        )
    )
    await _charge_compat_usage(
        account=account,
        usage_type=AccountUsageType.AI_IMAGE,
        usage_id=usage_id,
        credits_amount=Decimal("4"),
    )
    return {"source": response.content}


@router.post("/book/parse_article/")
async def parse_article(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    return {
        "title": "Article parsing is disabled in the DDD MVP",
        "text": "",
        "url": payload.get("url"),
        "disabled": True,
    }


@router.post("/book/parse_subtitles/")
async def parse_subtitles(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    return {"items": [], "url": payload.get("url"), "disabled": True}


@router.get("/book/{book_id:int}/")
async def get_book(
    book_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    book = await BookModel.get_or_none(id=book_id, account_id=account.id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await _serialize_book(book, account, with_chapters=True)


@router.patch("/book/{book_id:int}/")
async def update_book(
    book_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    book = await BookModel.get_or_none(id=book_id, account_id=account.id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if "name" in payload:
        book.name = _truncate(str(payload["name"]), 255)
    if "description" in payload:
        await _set_book_description(book, account, _first_str(payload.get("description")))
    image_path = _image_path_from_payload(payload)
    language_id = _safe_int(payload.get("language_id") or payload.get("language"))
    if language_id and await LanguageModel.get_or_none(id=language_id):
        book.language_id = language_id
    await book.save()
    if image_path:
        await BookModel.filter(id=book.id).update(image=image_path)
        book.__dict__["image"] = image_path
    if "is_active" in payload:
        state_obj = await _book_state(book, account)
        state_obj.is_active = _truthy(payload.get("is_active"), True)
        await state_obj.save()
    return await _serialize_book(book, account, with_chapters=True)


@router.delete("/book/{book_id:int}/")
async def delete_book(
    book_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    book = await BookModel.get_or_none(id=book_id, account_id=account.id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await book.delete()
    return {"id": book_id}


@router.post("/book/{book_id:int}/add_chapter/")
async def add_chapter(
    book_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    book = await BookModel.get_or_none(id=book_id, account_id=account.id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    chapter_input = payload.get("chapter_input") or {}
    text = str(chapter_input.get("text") or payload.get("text") or "")
    if not text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="chapter text is required")
    await _create_chapter(
        book=book,
        account=account,
        name=str(payload.get("name") or f"Chapter {book.chapters_count + 1}"),
        text=text,
        source_url=_source_url_from_payload(payload),
    )
    return await _serialize_book(book, account, with_chapters=True)


@router.post("/book/{book_id:int}/sort_chapters/")
async def sort_chapters(
    book_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    book = await BookModel.get_or_none(id=book_id, account_id=account.id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    ordering = payload.get("ordering") or []
    for position, chapter_id in enumerate(ordering):
        await ChapterModel.filter(id=_safe_int(chapter_id), book_id=book.id).update(position=position)
    return await _serialize_book(book, account, with_chapters=True)


@router.delete("/book/{book_id:int}/delete_chapter/")
async def delete_chapter(
    book_id: int,
    chapter: int = Query(...),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    book = await BookModel.get_or_none(id=book_id, account_id=account.id)
    chapter_obj = await ChapterModel.get_or_none(id=chapter, book_id=book_id, account_id=account.id)
    if not book or not chapter_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await chapter_obj.delete()
    book.chapters_count = await ChapterModel.filter(book_id=book.id).count()
    await book.save()
    return await _serialize_book(book, account, with_chapters=True)


@router.get("/chapter/")
async def list_chapters(
    page: int | None = Query(default=None),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    data = await _paginate(ChapterModel.filter(account_id=account.id).order_by("-id"), page)
    return {
        "count": data["count"],
        "results": [await _serialize_chapter(chapter, account) for chapter in data["results"]],
    }


@router.get("/chapter/{chapter_id:int}/")
async def get_chapter(
    chapter_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    chapter = await ChapterModel.get_or_none(id=chapter_id, account_id=account.id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await _serialize_chapter(chapter, account, with_content=True)


@router.patch("/chapter/{chapter_id:int}/")
async def update_chapter(
    chapter_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    chapter = await ChapterModel.get_or_none(id=chapter_id, account_id=account.id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if "name" in payload:
        chapter.name = _truncate(str(payload["name"]), 255)
    if _payload_has_source_url(payload):
        chapter.source_url = _source_url_from_payload(payload)
    if "name" in payload or _payload_has_source_url(payload):
        await chapter.save()
    return await _serialize_chapter(chapter, account, with_content=True)


@router.post("/chapter/{chapter_id:int}/set_percent/")
async def set_chapter_percent(
    chapter_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    chapter = await ChapterModel.get_or_none(id=chapter_id, account_id=account.id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    progress, _ = await CompatChapterProgressModel.get_or_create(
        account_id=account.id,
        chapter_id=chapter.id,
        defaults={"percent": 0},
    )
    progress.percent = max(0, min(100, _safe_int(payload.get("percent"))))
    await progress.save()
    return await _serialize_chapter(chapter, account, with_content=True)


@router.get("/text_part/")
async def list_text_parts(
    search: str | None = Query(default=None),
    chapter: int | None = Query(default=None),
    chapter_id: int | None = Query(default=None),
    account: AccountModel = Depends(_current_account),
) -> list[dict[str, Any]]:
    query = CompatTextPartModel.filter(account_id=account.id).order_by("-id")
    if search:
        query = query.filter(name__icontains=search)
    target_chapter_id = chapter or chapter_id
    if target_chapter_id:
        query = query.filter(chapter_id=target_chapter_id)
    text_parts = await query
    return [await _serialize_text_part(text_part, account) for text_part in text_parts]


@router.post("/text_part/")
async def create_text_part(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name is required")
    chapter_id = _safe_int(payload.get("chapter") or payload.get("chapter_id")) or None
    if not chapter_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="chapter is required")
    chapter = await ChapterModel.get_or_none(id=chapter_id, account_id=account.id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    language = await _word_language_from_chapter(chapter)
    translate_payload = payload.get("translate")
    description = _first_str(payload.get("description")) or None
    if isinstance(translate_payload, dict):
        translate = _first_str(translate_payload.get("translate")) or None
        if "description" in translate_payload and description is None:
            description = _first_str(translate_payload.get("description")) or None
    else:
        translate = _first_str(translate_payload) or None
    text_part = await CompatTextPartModel.create(
        account_id=account.id,
        chapter_id=chapter.id,
        language_id=language.id,
        name=name,
        translate=translate,
        transliteration=_first_str(payload.get("transliteration")) or None,
        description=description,
    )
    return await _serialize_text_part(text_part, account)


@router.get("/text_part/{text_part_id:int}/")
async def get_text_part(
    text_part_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    text_part = await CompatTextPartModel.get_or_none(id=text_part_id, account_id=account.id)
    if not text_part:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await _serialize_text_part(text_part, account)


@router.patch("/text_part/{text_part_id:int}/")
async def update_text_part(
    text_part_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    text_part = await CompatTextPartModel.get_or_none(id=text_part_id, account_id=account.id)
    if not text_part:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if "name" in payload:
        text_part.name = str(payload.get("name") or "").strip() or text_part.name
    if "transliteration" in payload:
        text_part.transliteration = _first_str(payload.get("transliteration")) or None
    if "description" in payload:
        text_part.description = _first_str(payload.get("description")) or None
    if "translate" in payload:
        translate_payload = payload.get("translate")
        if isinstance(translate_payload, dict):
            text_part.translate = _first_str(translate_payload.get("translate")) or None
            if "description" in translate_payload and "description" not in payload:
                text_part.description = _first_str(translate_payload.get("description")) or None
        else:
            text_part.translate = _first_str(translate_payload) or None
    await text_part.save()
    return await _serialize_text_part(text_part, account)


@router.post("/text_part/create_from_indexes/")
async def create_text_part_from_indexes(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    indexes = [_safe_int(item) for item in payload.get("indexes") or []]
    items = await _selected_word_chapters(indexes, account)
    text_part = await _create_text_part_from_word_chapters(
        items,
        account,
        payload.get("action"),
        payload.get("translate_type"),
    )
    await _publish_segment_event_for_text_part(indexes=indexes, payload=payload, account=account)
    return await _serialize_text_part(text_part, account)


@router.delete("/text_part/{text_part_id:int}/")
async def delete_text_part(
    text_part_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    deleted = await CompatTextPartModel.filter(id=text_part_id, account_id=account.id).delete()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {"id": text_part_id}


@router.get("/text_part/{text_part_id:int}/dialog/")
async def get_text_part_dialog(
    text_part_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    text_part = await CompatTextPartModel.get_or_none(id=text_part_id, account_id=account.id)
    if not text_part:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    dialog, _ = await CompatDialogModel.get_or_create(
        account_id=account.id,
        text_part_id=text_part.id,
        defaults={"dialog": []},
    )
    return {"id": dialog.id, "text_part": text_part.id, "dialog": dialog.dialog}


@router.post("/text_part/{text_part_id:int}/dialog/")
async def send_text_part_dialog_message(
    text_part_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    text_part = await CompatTextPartModel.get_or_none(id=text_part_id, account_id=account.id)
    if not text_part:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    dialog, _ = await CompatDialogModel.get_or_create(
        account_id=account.id,
        text_part_id=text_part.id,
        defaults={"dialog": []},
    )
    message = str(payload.get("message") or "").strip()
    if message:
        await _assert_ai_credits(account, Decimal("5"))
        history = list(dialog.dialog or [])
        history.append({"role": "user", "content": message})
        target_language = await _target_language(account)
        provider = await _reader_ai_provider_for_account(account)
        response = await provider.answer_dialog(
            ReaderDialogRequest(
                account_id=account.id,
                text_part_id=text_part.id,
                text_part=text_part.name,
                message=message,
                history=history,
                target_language_code=target_language.code,
            )
        )
        history.append(
            {
                "role": "assistant",
                "content": response.content,
            }
        )
        dialog.dialog = history
        await dialog.save()
        await _charge_compat_usage(
            account=account,
            usage_type=AccountUsageType.AI_DIALOG,
            usage_id=text_part.id,
            credits_amount=Decimal("5"),
    )
    return {"id": dialog.id, "text_part": text_part.id, "dialog": dialog.dialog}


@router.get("/phrase/")
async def list_phrases(
    search: str | None = Query(default=None),
    chapter: int | None = Query(default=None),
    chapter_id: int | None = Query(default=None),
    text_part: int | None = Query(default=None),
    text_part_id: int | None = Query(default=None),
    account: AccountModel = Depends(_current_account),
) -> list[dict[str, Any]]:
    query = CompatPhraseModel.filter(account_id=account.id).order_by("-id")
    if search:
        query = query.filter(name__icontains=search)
    target_chapter_id = chapter or chapter_id
    if target_chapter_id:
        query = query.filter(chapter_id=target_chapter_id)
    target_text_part_id = text_part or text_part_id
    if target_text_part_id:
        query = query.filter(text_part_id=target_text_part_id)
    phrases = await query
    return [await _serialize_phrase(phrase, account) for phrase in phrases]


@router.post("/phrase/")
async def create_phrase(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name is required")
    text_part_id = _safe_int(payload.get("text_part") or payload.get("text_part_id")) or None
    text_part: CompatTextPartModel | None = None
    if text_part_id:
        text_part = await CompatTextPartModel.get_or_none(id=text_part_id, account_id=account.id)
        if not text_part:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    chapter_id = _safe_int(payload.get("chapter") or payload.get("chapter_id")) or None
    if not chapter_id and text_part:
        chapter_id = text_part.chapter_id
    if not chapter_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="chapter is required")
    chapter = await ChapterModel.get_or_none(id=chapter_id, account_id=account.id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    language = await _word_language_from_chapter(chapter)
    translate_payload = payload.get("translate")
    description = _first_str(payload.get("description")) or None
    if isinstance(translate_payload, dict):
        translate = _first_str(translate_payload.get("translate")) or None
        if "description" in translate_payload and description is None:
            description = _first_str(translate_payload.get("description")) or None
    else:
        translate = _first_str(translate_payload) or None
    phrase = await CompatPhraseModel.create(
        account_id=account.id,
        chapter_id=chapter.id,
        language_id=language.id,
        text_part_id=text_part.id if text_part else None,
        name=name,
        translate=translate,
        transliteration=_first_str(payload.get("transliteration")) or None,
        description=description,
    )
    return await _serialize_phrase(phrase, account)


@router.get("/phrase/{phrase_id:int}/")
async def get_phrase(
    phrase_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    phrase = await CompatPhraseModel.get_or_none(id=phrase_id, account_id=account.id)
    if not phrase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await _serialize_phrase(phrase, account)


@router.patch("/phrase/{phrase_id:int}/")
async def update_phrase(
    phrase_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    phrase = await CompatPhraseModel.get_or_none(id=phrase_id, account_id=account.id)
    if not phrase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if "name" in payload:
        phrase.name = str(payload.get("name") or "").strip() or phrase.name
    if "transliteration" in payload:
        phrase.transliteration = _first_str(payload.get("transliteration")) or None
    if "description" in payload:
        phrase.description = _first_str(payload.get("description")) or None
    if "translate" in payload:
        translate_payload = payload.get("translate")
        if isinstance(translate_payload, dict):
            phrase.translate = _first_str(translate_payload.get("translate")) or None
            if "description" in translate_payload and "description" not in payload:
                phrase.description = _first_str(translate_payload.get("description")) or None
        else:
            phrase.translate = _first_str(translate_payload) or None
    await phrase.save()
    return await _serialize_phrase(phrase, account)


@router.get("/phrase/get_study_phrases/")
async def get_study_phrases(
    account: AccountModel = Depends(_current_account),
) -> list[dict[str, Any]]:
    studies = await CompatStudyPhraseModel.filter(
        account_id=account.id,
        is_active=True,
    ).order_by("-id")
    result: list[dict[str, Any]] = []
    for study in studies:
        if study.phrase_id:
            phrase = await CompatPhraseModel.get(id=study.phrase_id)
            result.append(await _serialize_phrase(phrase, account))
    return result


@router.post("/phrase/create_from_indexes/")
async def create_phrase_from_indexes(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> list[dict[str, Any]]:
    phrases: list[dict[str, Any]] = []
    for indexes in payload.get("indexes_list") or []:
        items = await _selected_word_chapters([_safe_int(item) for item in indexes], account)
        phrase = await _create_phrase_from_word_chapters(items, account, payload.get("action"))
        phrases.append(await _serialize_phrase(phrase, account))
    return phrases


@router.get("/phrase/load_for_text_part/")
async def load_phrases_for_text_part(
    text_part: int | None = Query(default=None),
    text_part_id: int | None = Query(default=None),
    account: AccountModel = Depends(_current_account),
) -> list[dict[str, Any]]:
    target_id = text_part or text_part_id
    if not target_id:
        return []
    phrases = await CompatPhraseModel.filter(
        account_id=account.id,
        text_part_id=target_id,
    ).order_by("id")
    return [await _serialize_phrase(phrase, account) for phrase in phrases]


@router.delete("/phrase/{phrase_id:int}/")
async def delete_phrase(
    phrase_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    deleted = await CompatPhraseModel.filter(id=phrase_id, account_id=account.id).delete()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {"id": phrase_id}


@router.get("/phrase/{phrase_id:int}/create_voice/")
async def create_phrase_voice(
    phrase_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    phrase = await CompatPhraseModel.get_or_none(id=phrase_id, account_id=account.id)
    if not phrase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    should_charge = not phrase.ai_voice_file
    if should_charge:
        source_language = await LanguageModel.get(id=phrase.language_id)
        voice_result = await _voice_file_result(
            "phrase",
            phrase.id,
            phrase.name,
            account,
            source_language,
            required_credits=Decimal("0.50"),
        )
        if voice_result.billable:
            phrase.ai_voice_file = voice_result.file_path
            await phrase.save()
            await _charge_compat_usage(
                account=account,
                usage_type=AccountUsageType.AI_VOICE,
                usage_id=phrase.id,
                credits_amount=Decimal("0.50"),
            )
    return await _serialize_phrase(phrase, account)


@router.get("/word/")
async def list_words(account: AccountModel = Depends(_current_account)) -> list[dict[str, Any]]:
    words = await WordTranslateModel.filter(account_id=account.id).order_by("id")
    return [await _serialize_word_translate(word, account) for word in words]


@router.get("/word/{word_translate_id:int}/")
async def get_word(
    word_translate_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    word_translate = await _get_word_translate_or_404(word_translate_id, account)
    return await _serialize_word_translate(word_translate, account)


@router.get("/word/{word_translate_id:int}/create_etymology/")
async def create_word_etymology(
    word_translate_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    word_translate = await _get_word_translate_or_404(
        word_translate_id,
        account,
        required_ai_credits=Decimal("10"),
    )
    word = await WordModel.get(id=word_translate.word_id)
    should_charge = not await CompatWordEtymologyModel.get_or_none(word_id=word.id)
    if should_charge:
        await _assert_ai_credits(account, Decimal("10"))
    await _ensure_etymology(word, account)
    if should_charge:
        await _charge_compat_usage(
            account=account,
            usage_type=AccountUsageType.AI_WORD,
            usage_id=word_translate.id,
            credits_amount=Decimal("10"),
        )
    return await _serialize_word_translate(word_translate, account)


@router.get("/word/{word_translate_id:int}/get_etymology/")
async def get_word_etymology(
    word_translate_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    word_translate = await _get_word_translate_or_404(
        word_translate_id,
        account,
        ensure_missing=False,
    )
    return await _serialize_word_translate(word_translate, account)


@router.get("/study_phrase/")
async def list_study_phrases(
    page: int | None = Query(default=None),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    data = await _paginate(
        CompatStudyPhraseModel.filter(account_id=account.id).order_by("-id"),
        page,
    )
    return {
        "count": data["count"],
        "results": [await _serialize_study_phrase(study, account) for study in data["results"]],
    }


@router.post("/study_phrase/")
async def create_study_phrase(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    word_id = _safe_int(payload.get("word_id")) or None
    phrase_id = _safe_int(payload.get("phrase_id")) or None
    text_part_id = _safe_int(payload.get("text_part_id")) or None
    chapter_id = _safe_int(payload.get("chapter_id")) or None
    study = await CompatStudyPhraseModel.create(
        account_id=account.id,
        chapter_id=chapter_id,
        word_id=word_id,
        phrase_id=phrase_id,
        text_part_id=text_part_id,
        is_active=_truthy(payload.get("is_active"), True),
    )
    return await _serialize_study_phrase(study, account)


@router.get("/study_phrase/{study_id:int}/")
async def get_study_phrase(
    study_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    study = await CompatStudyPhraseModel.get_or_none(id=study_id, account_id=account.id)
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await _serialize_study_phrase(study, account)


@router.patch("/study_phrase/{study_id:int}/")
async def update_study_phrase(
    study_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    study = await CompatStudyPhraseModel.get_or_none(id=study_id, account_id=account.id)
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if "is_active" in payload:
        study.is_active = _truthy(payload.get("is_active"), True)
    if payload.get("chapter_id"):
        study.chapter_id = _safe_int(payload.get("chapter_id"))
    await study.save()
    return await _serialize_study_phrase(study, account)


@router.delete("/study_phrase/{study_id:int}/")
async def delete_study_phrase(
    study_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    deleted = await CompatStudyPhraseModel.filter(id=study_id, account_id=account.id).delete()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {"id": study_id}


@router.get("/study_phrase/check_exist/")
async def check_study_phrase_exist(
    word_id: str | None = Query(default=None),
    phrase_id: str | None = Query(default=None),
    text_part_id: str | None = Query(default=None),
    account: AccountModel = Depends(_current_account),
) -> list[Any]:
    field, raw_ids = next(
        (
            (name, value)
            for name, value in (
                ("word_id", word_id),
                ("phrase_id", phrase_id),
                ("text_part_id", text_part_id),
            )
            if value
        ),
        ("word_id", ""),
    )
    ids = [_safe_int(item) for item in str(raw_ids).split(",") if _safe_int(item)]
    result: dict[int, list[Any]] = {}
    for item_id in ids:
        filters = {"account_id": account.id, field: item_id}
        study = await CompatStudyPhraseModel.get_or_none(**filters)
        result[item_id] = [study.id, study.is_active] if study else [None, False]
    return [field, result]


@router.post("/study_phrase/create_word_voice/")
async def create_word_voice(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    word_id = _safe_int(payload.get("id") or payload.get("word_id"))
    word = await WordModel.get_or_none(id=word_id)
    if not word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    voice = await WordVoiceModel.get_or_none(word_id=word.id)
    should_charge = False
    if not voice or not voice.file_path:
        source_language = await LanguageModel.get(id=word.language_id)
        voice_result = await _voice_file_result(
            "word",
            word.id,
            word.name,
            account,
            source_language,
            required_credits=Decimal("0.50"),
        )
        if voice_result.billable:
            if voice:
                voice.file_path = voice_result.file_path
                await voice.save()
            else:
                voice = await WordVoiceModel.create(
                    word_id=word.id,
                    file_path=voice_result.file_path,
                )
            should_charge = True
    if should_charge:
        await _charge_compat_usage(
            account=account,
            usage_type=AccountUsageType.AI_VOICE,
            usage_id=word.id,
            credits_amount=Decimal("0.50"),
        )
    return await _serialize_word_model(word, account)


@router.get("/study_phrase/{study_id:int}/create_voice/")
async def create_study_phrase_voice(
    study_id: int,
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    study = await CompatStudyPhraseModel.get_or_none(id=study_id, account_id=account.id)
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    should_charge = False
    if study.word_id:
        word = await WordModel.get(id=study.word_id)
        voice = await WordVoiceModel.get_or_none(word_id=word.id)
        if not voice or not voice.file_path:
            source_language = await LanguageModel.get(id=word.language_id)
            voice_result = await _voice_file_result(
                "word",
                word.id,
                word.name,
                account,
                source_language,
                required_credits=Decimal("0.50"),
            )
            if voice_result.billable:
                if voice:
                    voice.file_path = voice_result.file_path
                    await voice.save()
                else:
                    voice = await WordVoiceModel.create(
                        word_id=word.id,
                        file_path=voice_result.file_path,
                    )
                should_charge = True
    if study.text_part_id:
        text_part = await CompatTextPartModel.get(id=study.text_part_id)
        if not text_part.ai_voice_file:
            source_language = await LanguageModel.get(id=text_part.language_id)
            voice_result = await _voice_file_result(
                "text_part",
                text_part.id,
                text_part.name,
                account,
                source_language,
                required_credits=Decimal("0.50"),
            )
            if voice_result.billable:
                text_part.ai_voice_file = voice_result.file_path
                await text_part.save()
                should_charge = True
    if study.phrase_id:
        phrase = await CompatPhraseModel.get(id=study.phrase_id)
        if not phrase.ai_voice_file:
            source_language = await LanguageModel.get(id=phrase.language_id)
            voice_result = await _voice_file_result(
                "phrase",
                phrase.id,
                phrase.name,
                account,
                source_language,
                required_credits=Decimal("0.50"),
            )
            if voice_result.billable:
                phrase.ai_voice_file = voice_result.file_path
                await phrase.save()
                should_charge = True
    if should_charge:
        await _charge_compat_usage(
            account=account,
            usage_type=AccountUsageType.AI_VOICE,
            usage_id=study.id,
            credits_amount=Decimal("0.50"),
        )
    return await _serialize_study_phrase(study, account)


@router.get("/transaction/")
async def list_transactions(
    page: int | None = Query(default=None),
    transaction_type: str | None = Query(default=None),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    query = AccountTransactionModel.filter(account_id=account.id).order_by("-id")
    if transaction_type:
        query = query.filter(transaction_type__in=transaction_type.split(","))
    data = await _paginate(query, page)
    return {
        "count": data["count"],
        "results": [await _serialize_transaction(item) for item in data["results"]],
    }


@router.post("/telegram/update/")
async def receive_telegram_update(
    payload: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    callback_query = payload.get("callback_query") or {}
    callback_data = str(callback_query.get("data") or "")
    manual_bill_match = MANUAL_BILL_CALLBACK_RE.match(callback_data)
    if manual_bill_match:
        result = await _handle_manual_bill_callback(
            payload=payload,
            bill_id=_safe_int(manual_bill_match.group("bill_id")),
            answer=manual_bill_match.group("answer"),
        )
        await _send_telegram_result_from_update(payload, result)
        return result
    callback_match = STUDY_PHRASE_LOG_CALLBACK_RE.match(callback_data)
    if callback_match:
        return await _rate_study_phrase_log(
            log_id=_safe_int(callback_match.group("log_id")),
            rank=_safe_int(callback_match.group("rank")),
            callback_query=callback_query,
        )
    action_match = STUDY_TASK_ACTION_CALLBACK_RE.match(callback_data)
    if action_match:
        action = _safe_int(action_match.group("action"), -1)
        if action == STUDY_TASK_DELETE_ACTION:
            return await _handle_study_task_delete_callback(payload)
        if action not in STUDY_TASK_ACTION_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported study task action")
        return await _create_study_task_from_telegram_update(
            payload=payload,
            requested_type=STUDY_TASK_ACTION_TYPES[action],
        )

    pre_checkout = payload.get("pre_checkout_query") or {}
    if pre_checkout:
        bill_id = _safe_int(pre_checkout.get("invoice_payload"))
        if not bill_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invoice_payload is required")
        result = await TelegramBot._base_payment_checkout(bill_id=bill_id)
        return {
            "success": result.success,
            "handled": "pre_checkout",
            "bill_id": bill_id,
            "message": result.message,
        }

    message = payload.get("message") or {}
    command_parts = str(message.get("text") or "").split(maxsplit=1)
    command = (command_parts[0] if command_parts else "").split("@", 1)[0].lower()
    if _admin_bonus_match(str(message.get("text") or "")):
        return await _create_admin_bonus_from_telegram_update(payload)
    if MANUAL_CREDITS_MESSAGE_RE.match(str(message.get("text") or "")):
        result = await _create_manual_bill_from_telegram_update(payload)
        await _send_telegram_result_from_update(payload, result)
        return result
    if command in HELP_COMMANDS or command in ADMIN_CREDIT_COMMANDS:
        return await _handle_telegram_help_from_update(payload)
    if command == "/start":
        result = await _handle_start_from_telegram_update(payload)
        await _send_telegram_result_from_update(payload, result)
        return result
    if command == "/start_bonus":
        result = await _handle_start_bonus_from_telegram_update(payload)
        await _send_telegram_result_from_update(payload, result)
        return result
    if command == "/users":
        result = await _handle_users_stats_from_telegram_update(payload)
        await _send_telegram_result_from_update(payload, result)
        return result
    if command == "/stats":
        result = await _handle_payment_stats_from_telegram_update(payload)
        await _send_telegram_result_from_update(payload, result)
        return result
    if command == "/task":
        return await _create_study_task_from_telegram_update(payload=payload, requested_type=None)
    if command == "/reset_tasks":
        result = await _reset_study_tasks_from_telegram_update(payload)
        await _send_telegram_result_from_update(payload, result)
        return result

    successful_payment_payload = message.get("successful_payment") or {}
    if successful_payment_payload:
        try:
            successful_payment = SuccessfulPayment.model_validate(successful_payment_payload)
            bill_id = int(successful_payment.invoice_payload)
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="valid successful_payment.invoice_payload is required",
            ) from exc
        result = await TelegramBot._base_payment_successful(
            bill_id=bill_id,
            transaction=successful_payment.telegram_payment_charge_id,
            payment_data=successful_payment.model_dump(),
        )
        return {
            "success": result.success,
            "handled": "successful_payment",
            "bill_id": bill_id,
        }

    if command.startswith("/"):
        return await _handle_unknown_telegram_command(payload, command)

    return {"success": True, "handled": None}


@router.post("/transaction/start_bonus/")
async def start_bonus(account: AccountModel = Depends(_current_account)) -> dict[str, Any]:
    exists = await AccountTransactionModel.get_or_none(
        account_id=account.id,
        transaction_type=TransactionType.START_BONUS,
    )
    if exists:
        return {"success": False, "message": "Start bonus already exists"}
    await _create_transaction(account, TransactionType.START_BONUS, Decimal(settings.credits_start_bonus))
    return {"success": True, "message": "Start bonus granted"}


@router.post("/transaction/send_tg_payment/")
async def send_tg_payment(
    payload: dict[str, Any] = Body(default_factory=dict),
    account: AccountModel = Depends(_current_account),
) -> dict[str, Any]:
    cost = max(1, _safe_int(payload.get("cost"), 1))
    bill = await BillModel.create(
        account_id=account.id,
        credits_amount=Decimal(cost),
        cost=cost,
        currency=Currency.STAR,
        payment_service=PaymentService.TG_STARS,
        payment_data={"local_status": "created"},
    )
    invoice_sent, invoice_error = await _send_telegram_stars_invoice(account, bill, cost)
    bill.payment_data = {
        **(bill.payment_data or {}),
        "invoice_sent": invoice_sent,
        "invoice_error": invoice_error,
    }
    await bill.save()
    return {
        "success": True,
        "bill_id": bill.id,
        "invoice_payload": str(bill.id),
        "invoice_sent": invoice_sent,
        "message": (
            "Telegram Stars invoice sent."
            if invoice_sent
            else "Local Telegram Stars bill created; invoice delivery failed."
        ),
    }


@router.get("/transaction/get_referral_code/")
async def get_referral_code(account: AccountModel = Depends(_current_account)) -> dict[str, Any]:
    referral_code = _compat_referral_code(account)
    base = _telegram_web_app_root_url().rstrip("/")
    display_name = account.public_name or account.username
    return {
        "id": account.id,
        "name": f"Base {display_name}",
        "code": referral_code,
        "percentage": REFERRAL_PERCENTAGE,
        "create_time": account.created_at,
        "referral_url": f"{base}?start=ref_{referral_code}",
        "startapp_url": f"{base}?startapp={referral_code}",
    }


@router.get("/transaction/get_referrals/")
async def get_referrals(account: AccountModel = Depends(_current_account)) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    profiles = await AuthProfileModel.filter(
        provider_type=AuthProviderType.TELEGRAM,
    ).order_by("-id")
    for profile in profiles:
        data = profile.provider_data or {}
        referral = data.get(REFERRAL_PROFILE_KEY)
        if not isinstance(referral, dict):
            continue
        if _safe_int(referral.get("account_id")) != account.id:
            continue
        referred_account = await AccountModel.get_or_none(id=profile.account_id)
        if not referred_account:
            continue
        result.append(
            {
                "id": profile.id,
                "referral": await _serialize_account(referred_account),
                "create_time": referral.get("create_time") or profile.created_at,
                "percentage": _safe_int(referral.get("percentage"), REFERRAL_PERCENTAGE),
                "earned_amount": 0,
            }
        )
    return result
