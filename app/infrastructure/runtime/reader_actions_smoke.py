from __future__ import annotations

import random
import time
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from infrastructure.runtime.legacy_compat_smoke import JsonHttpClient


UploadFetcher = Callable[[str], dict[str, Any]]


@dataclass(frozen=True)
class ReaderActionsSmokeStep:
    name: str
    ok: bool
    error_message: str | None = None


@dataclass(frozen=True)
class ReaderActionsSmokeResult:
    ok: bool
    api_root: str
    tg_user_id: int
    steps: tuple[ReaderActionsSmokeStep, ...]
    summary: dict[str, Any]
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "api_root": self.api_root,
            "tg_user_id": self.tg_user_id,
            "steps": [asdict(step) for step in self.steps],
            "summary": self.summary,
            "error_message": self.error_message,
        }


class UrllibUploadFetcher:
    def __init__(self, server_root: str, timeout_seconds: int = 20) -> None:
        self._server_root = server_root.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._ngrok_headers = (
            {"ngrok-skip-browser-warning": "true"}
            if "ngrok.app" in self._server_root
            else {}
        )

    def __call__(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self._server_root}{path}",
            headers=self._ngrok_headers,
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            body = response.read()
            return {
                "path": path,
                "status": int(response.status),
                "content_type": response.headers.get("content-type", ""),
                "byte_length": len(body),
            }


def run_reader_actions_smoke(
    *,
    client: JsonHttpClient,
    api_root: str,
    tg_user_id: int | None = None,
    seed: str | None = None,
    chapter_ready_attempts: int = 70,
    chapter_ready_delay_seconds: float = 1.5,
    sleep: Callable[[float], object] = time.sleep,
    check_upload_files: bool = False,
    upload_fetcher: UploadFetcher | None = None,
) -> ReaderActionsSmokeResult:
    effective_tg_user_id = tg_user_id or 992000000 + random.randint(0, 999999)
    effective_seed = seed or f"{effective_tg_user_id}_{int(time.time() * 1000)}"
    steps: list[ReaderActionsSmokeStep] = []
    summary: dict[str, Any] = {}
    token: str | None = None
    upload_checks: dict[str, Any] = {}

    def step(name: str, action: Callable[[], Any]) -> Any:
        try:
            value = action()
        except Exception as exc:
            steps.append(
                ReaderActionsSmokeStep(name=name, ok=False, error_message=str(exc)),
            )
            raise
        steps.append(ReaderActionsSmokeStep(name=name, ok=True))
        return value

    try:
        auth, language = step(
            "auth_language",
            lambda: _check_auth_language(client, effective_tg_user_id),
        )
        token = auth["token"]
        summary["account_id"] = auth["account"]["id"]
        summary["language_id"] = language["id"]

        book, base_chapter, generated_chapter, image, generation_summary = step(
            "ai_generation_contract",
            lambda: _check_ai_generation_contract(
                client,
                token,
                language["id"],
                effective_seed,
                chapter_ready_attempts,
                chapter_ready_delay_seconds,
                sleep,
            ),
        )
        summary["book_id"] = book["id"]
        summary["base_chapter_id"] = base_chapter["id"]
        summary["generated_chapter_id"] = generated_chapter["id"]
        summary["image_source_prefix"] = str(image.get("source", ""))[:22]
        summary.update(generation_summary)

        text_part = step(
            "text_dialog_contract",
            lambda: _check_text_dialog_contract(client, token, base_chapter),
        )
        summary["text_part_id"] = text_part["id"]

        text_part_voice = step(
            "text_part_voice_contract",
            lambda: _check_text_part_voice_contract(client, token, base_chapter),
        )
        summary["text_part_voice_id"] = text_part_voice["id"]
        summary["text_part_voice_file"] = text_part_voice["ai_voice"]["file"]

        phrase, word, phrase_voice, word_voice, word_summary = step(
            "word_phrase_voice_etymology_contract",
            lambda: _check_word_phrase_voice_etymology_contract(
                client,
                token,
                base_chapter,
                text_part,
            ),
        )
        summary["phrase_id"] = phrase["id"]
        summary["word_id"] = word["word"]["id"]
        summary["word_translate_id"] = word["id"]
        summary.update(word_summary)
        summary["phrase_voice_file"] = phrase_voice["ai_voice"]["file"]
        summary["word_voice_file"] = word_voice["ai_voice"]["file"]

        if check_upload_files:
            fetcher = upload_fetcher
            _require(fetcher is not None, "upload_fetcher is required")
            upload_checks["text_part"] = _check_upload_file(
                fetcher,
                text_part_voice["ai_voice"]["file"],
                "text part voice",
            )
            upload_checks["phrase"] = _check_upload_file(
                fetcher,
                phrase_voice["ai_voice"]["file"],
                "phrase voice",
            )
            upload_checks["word"] = _check_upload_file(
                fetcher,
                word_voice["ai_voice"]["file"],
                "word voice",
            )
            summary["upload_checks"] = upload_checks

        study, transactions = step(
            "study_voice_transactions_contract",
            lambda: _check_study_voice_transactions_contract(
                client,
                token,
                base_chapter,
                text_part,
                phrase,
                word,
            ),
        )
        summary["study_id"] = study["id"]
        summary["ai_usage_transaction_count"] = transactions.get("count")
    except Exception as exc:
        return ReaderActionsSmokeResult(
            ok=False,
            api_root=api_root.rstrip("/"),
            tg_user_id=effective_tg_user_id,
            steps=tuple(steps),
            summary=summary,
            error_message=str(exc),
        )

    return ReaderActionsSmokeResult(
        ok=True,
        api_root=api_root.rstrip("/"),
        tg_user_id=effective_tg_user_id,
        steps=tuple(steps),
        summary=summary,
    )


def _check_auth_language(
    client: JsonHttpClient,
    tg_user_id: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    auth = client.request(
        "POST",
        "/account/telegram_auth/",
        body={
            "auth_data": {
                "user": {
                    "id": tg_user_id,
                    "first_name": "Reader",
                    "last_name": "Actions",
                    "username": f"reader_actions_{tg_user_id}",
                    "language_code": "en",
                },
            },
        },
    ).data
    _require(auth.get("token"), f"telegram_auth did not return token: {auth}")
    _require(auth.get("account", {}).get("id"), f"telegram_auth has no account: {auth}")
    languages = client.request("GET", "/language/", token=auth["token"]).data
    language = _first_item(languages)
    _require(language.get("id"), f"No language in /language/: {languages}")
    return auth, language


def _check_ai_generation_contract(
    client: JsonHttpClient,
    token: str,
    language_id: int,
    seed: str,
    chapter_ready_attempts: int,
    chapter_ready_delay_seconds: float,
    sleep: Callable[[float], object],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    generated_book_payload = {
        "language_id": language_id,
        "language_level": "a1",
        "chapter_type": "story",
        "description": (
            f"Reader actions smoke {seed}. "
            "Generate enough words for dialog voice and etymology."
        ),
    }
    generated = client.request(
        "POST",
        "/book/generate/",
        token=token,
        body=generated_book_payload,
    ).data
    book = _first_item(generated)
    _require(book.get("id"), f"Generated book response has no book: {generated}")
    first_chapter_id = _chapter_id(_first_item(book.get("chapters") or []))
    _require(first_chapter_id, f"Generated book has no chapter: {book}")
    base_chapter = _wait_for_ready_chapter(
        client,
        token,
        first_chapter_id,
        chapter_ready_attempts,
        chapter_ready_delay_seconds,
        8,
        sleep,
    )

    generated_chapters_payload = {
        "book_id": book["id"],
        "language_id": language_id,
        "language_level": "a1",
        "chapter_type": "story",
        "description": f"Generated reader action chapter {seed}.",
    }
    with_chapter = client.request(
        "POST",
        "/book/generate_chapters/",
        token=token,
        body=generated_chapters_payload,
    ).data
    newest_chapter_id = max(
        _chapter_id(item)
        for item in with_chapter.get("chapters", [])
        if _chapter_id(item)
    )
    _require(newest_chapter_id, f"Generated chapters response has no chapter: {with_chapter}")
    generated_chapter = _wait_for_ready_chapter(
        client,
        token,
        newest_chapter_id,
        chapter_ready_attempts,
        chapter_ready_delay_seconds,
        8,
        sleep,
    )

    image = client.request(
        "POST",
        "/book/generate_image/",
        token=token,
        body={"name": book.get("name", ""), "description": f"Reader actions {seed}"},
    ).data
    _require(
        str(image.get("source", "")).startswith("data:image/"),
        f"AI image generation did not return data URL: {image}",
    )
    return book, base_chapter, generated_chapter, image, {
        "generated_book_payload_language_id": generated_book_payload["language_id"],
        "generated_book_payload_language_level": generated_book_payload["language_level"],
        "generated_book_payload_chapter_type": generated_book_payload["chapter_type"],
        "generated_chapters_payload_language_id": generated_chapters_payload["language_id"],
        "generated_chapters_payload_language_level": generated_chapters_payload[
            "language_level"
        ],
        "generated_chapters_payload_chapter_type": generated_chapters_payload[
            "chapter_type"
        ],
    }


def _check_text_dialog_contract(
    client: JsonHttpClient,
    token: str,
    chapter: dict[str, Any],
) -> dict[str, Any]:
    indexes = _word_indexes(chapter, 6)
    text_part = client.request(
        "POST",
        "/text_part/create_from_indexes/",
        token=token,
        body={"indexes": indexes, "action": "translate"},
    ).data
    _require(
        text_part.get("id")
        and text_part.get("words")
        and text_part.get("translate", {}).get("translate"),
        f"Text part create contract failed: {text_part}",
    )
    empty_dialog = client.request(
        "GET",
        f"/text_part/{text_part['id']}/dialog/",
        token=token,
    ).data
    _require(isinstance(empty_dialog.get("dialog"), list), f"Dialog load failed: {empty_dialog}")
    dialog = client.request(
        "POST",
        f"/text_part/{text_part['id']}/dialog/",
        token=token,
        body={"message": "Explain it."},
    ).data
    roles = {item.get("role") for item in dialog.get("dialog", [])}
    _require(
        {"user", "assistant"}.issubset(roles),
        f"Dialog send contract failed: {dialog}",
    )
    return text_part


def _check_text_part_voice_contract(
    client: JsonHttpClient,
    token: str,
    chapter: dict[str, Any],
) -> dict[str, Any]:
    indexes = _word_indexes(chapter, 6)
    text_part_voice = client.request(
        "POST",
        "/text_part/create_from_indexes/",
        token=token,
        body={"indexes": indexes, "action": "create_voice"},
    ).data
    _require(
        text_part_voice.get("id")
        and text_part_voice.get("words")
        and _is_upload_path(text_part_voice.get("ai_voice", {}).get("file")),
        f"Text part voice contract failed: {text_part_voice}",
    )
    return text_part_voice


def _check_word_phrase_voice_etymology_contract(
    client: JsonHttpClient,
    token: str,
    chapter: dict[str, Any],
    text_part: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    indexes = _word_indexes(chapter, 4)[1:4]
    phrase_payload = client.request(
        "POST",
        "/phrase/create_from_indexes/",
        token=token,
        body={"indexes_list": [indexes], "action": "translate"},
    ).data
    phrase = _first_item(phrase_payload)
    _require(
        phrase.get("id") and phrase.get("words"),
        f"Phrase create contract failed: {phrase_payload}",
    )

    phrase_voice = client.request(
        "GET",
        f"/phrase/{phrase['id']}/create_voice/",
        token=token,
    ).data
    _require(
        _is_upload_path(phrase_voice.get("ai_voice", {}).get("file")),
        f"Phrase voice contract failed: {phrase_voice}",
    )

    word_id = _first_word_id(chapter)
    word = client.request("GET", f"/word/{word_id}/", token=token).data
    _require(
        word.get("id") and word.get("word", {}).get("id") == word_id,
        f"Word detail contract failed: {word}",
    )
    _require_word_translate_render_shape(word, label="word detail")
    etymology = client.request(
        "GET",
        f"/word/{word['id']}/create_etymology/",
        token=token,
    ).data
    _require(
        etymology.get("ai_word") is True
        and etymology.get("word", {}).get("etymology", {}).get("description"),
        f"Etymology create failed: {etymology}",
    )
    _require_word_translate_render_shape(etymology, label="created etymology")
    loaded_etymology = client.request(
        "GET",
        f"/word/{word['id']}/get_etymology/",
        token=token,
    ).data
    _require(
        loaded_etymology.get("word", {}).get("root"),
        f"Etymology load failed: {loaded_etymology}",
    )
    _require_word_translate_render_shape(loaded_etymology, label="loaded etymology")
    word_voice = client.request(
        "POST",
        "/study_phrase/create_word_voice/",
        token=token,
        body={"id": word_id},
    ).data
    _require(
        _is_upload_path(word_voice.get("ai_voice", {}).get("file")),
        f"Word voice contract failed: {word_voice}",
    )
    root = loaded_etymology["word"]["root"]
    return phrase, word, phrase_voice, word_voice, {
        "word_render_type": word["type"],
        "word_render_name": word["word"]["name"],
        "word_render_translate": word["translate"],
        "word_render_transliteration": word["transliteration"],
        "word_etymology_root_name": root["name"],
        "word_etymology_root_description": root["translate"]["description"],
        "word_etymology_part_count": len(loaded_etymology["word"]["word_parts"]),
    }


def _require_word_translate_render_shape(value: dict[str, Any], *, label: str) -> None:
    nested_word = value.get("word")
    _require(
        value.get("id")
        and isinstance(value.get("type"), str)
        and isinstance(value.get("translate"), str)
        and isinstance(value.get("transliteration"), str)
        and isinstance(value.get("ai_word"), bool)
        and isinstance(nested_word, dict)
        and nested_word.get("id")
        and isinstance(nested_word.get("name"), str)
        and "ai_voice" in nested_word
        and isinstance(nested_word.get("word_parts"), list)
        and isinstance(nested_word.get("related_words"), list),
        f"{label} word render shape failed: {value}",
    )
    root = nested_word.get("root")
    if root is not None:
        _require(
            isinstance(root, dict)
            and isinstance(root.get("name"), str)
            and isinstance(root.get("translate"), dict)
            and isinstance(root["translate"].get("description"), str),
            f"{label} root render shape failed: {value}",
        )
    etymology = nested_word.get("etymology")
    if etymology is not None:
        _require(
            isinstance(etymology, dict)
            and isinstance(etymology.get("description"), str),
            f"{label} etymology render shape failed: {value}",
        )


def _check_study_voice_transactions_contract(
    client: JsonHttpClient,
    token: str,
    chapter: dict[str, Any],
    text_part: dict[str, Any],
    phrase: dict[str, Any],
    word: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    study = client.request(
        "POST",
        "/study_phrase/",
        token=token,
        body={
            "is_active": True,
            "chapter_id": chapter["id"],
            "word_id": word["word"]["id"],
            "text_part_id": text_part["id"],
            "phrase_id": phrase["id"],
        },
    ).data
    _require(
        study.get("id") and study.get("word") and study.get("text_part") and study.get("phrase"),
        f"Study create failed: {study}",
    )
    voiced_study = client.request(
        "GET",
        f"/study_phrase/{study['id']}/create_voice/",
        token=token,
    ).data
    _require(
        voiced_study.get("id") == study["id"],
        f"Study voice returned wrong item: {voiced_study}",
    )
    study_list = client.request("GET", "/study_phrase/", token=token).data
    _require(
        study_list.get("count", 0) >= 1
        and any(item.get("id") == study["id"] for item in study_list.get("results", [])),
        f"Study list misses created item: {study_list}",
    )
    transactions = client.request(
        "GET",
        "/transaction/?transaction_type=ai_usage",
        token=token,
    ).data
    _require(
        isinstance(transactions.get("count"), int) and transactions["count"] >= 1,
        f"AI usage transaction list failed: {transactions}",
    )
    return study, transactions


def _check_upload_file(
    upload_fetcher: UploadFetcher,
    path: str,
    label: str,
) -> dict[str, Any]:
    _require(_is_upload_path(path), f"{label} path is not an upload path: {path}")
    result = upload_fetcher(path)
    _require(
        result.get("status") in {200, 206},
        f"{label} upload status failed: {result}",
    )
    _require(
        int(result.get("byte_length") or 0) > 100,
        f"{label} upload is too small: {result}",
    )
    return result


def _wait_for_ready_chapter(
    client: JsonHttpClient,
    token: str,
    chapter_id: int,
    attempts: int,
    delay_seconds: float,
    min_tokens: int,
    sleep: Callable[[float], object],
) -> dict[str, Any]:
    latest: dict[str, Any] | None = None
    for attempt in range(attempts):
        latest = client.request("GET", f"/chapter/{chapter_id}/", token=token).data
        if (
            latest.get("is_ready") is True
            and isinstance(latest.get("content"), list)
            and len(latest["content"]) >= min_tokens
        ):
            return latest
        if attempt + 1 < attempts:
            sleep(delay_seconds)
    raise RuntimeError(f"Chapter {chapter_id} was not ready: {latest}")


def _first_item(value: Any) -> dict[str, Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value[0] if value else {}
    if isinstance(value, dict):
        results = value.get("results")
        if isinstance(results, list) and results:
            return results[0]
    return {}


def _chapter_id(value: Any) -> int:
    if isinstance(value, dict):
        return int(value.get("id") or 0)
    if isinstance(value, int):
        return value
    return 0


def _word_indexes(chapter: dict[str, Any], count: int) -> list[int]:
    indexes = [
        int(item["id"])
        for item in chapter.get("content", [])
        if item.get("id") and item.get("w")
    ][:count]
    _require(len(indexes) >= count, f"Not enough word tokens: {chapter}")
    return indexes


def _first_word_id(chapter: dict[str, Any]) -> int:
    for item in chapter.get("content", []):
        if item.get("w"):
            return int(item["w"])
    raise RuntimeError(f"Ready chapter has no word token: {chapter}")


def _is_upload_path(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("/uploads/")


def _require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)
