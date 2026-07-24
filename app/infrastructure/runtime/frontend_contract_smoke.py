from __future__ import annotations

import random
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from infrastructure.runtime.legacy_compat_smoke import JsonHttpClient


CONTRACT_BOOK_IMAGE: dict[str, Any] = {
    "name": "contract-cover.png",
    "type": "image/png",
    "size": 68,
    "content": (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+"
        "M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    ),
}

CONTRACT_BOOK_PATCH_IMAGE: dict[str, Any] = {
    **CONTRACT_BOOK_IMAGE,
    "name": "contract-cover-patched.png",
}


@dataclass(frozen=True)
class FrontendContractSmokeStep:
    name: str
    ok: bool
    error_message: str | None = None


@dataclass(frozen=True)
class FrontendContractSmokeResult:
    ok: bool
    api_root: str
    tg_user_id: int
    steps: tuple[FrontendContractSmokeStep, ...]
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


def run_frontend_contract_smoke(
    *,
    client: JsonHttpClient,
    api_root: str,
    tg_user_id: int | None = None,
    seed: str | None = None,
    chapter_ready_attempts: int = 70,
    chapter_ready_delay_seconds: float = 1.5,
    sleep: Callable[[float], object] = time.sleep,
) -> FrontendContractSmokeResult:
    effective_tg_user_id = tg_user_id or 994000000 + random.randint(0, 999999)
    effective_seed = seed or f"{effective_tg_user_id}_{int(time.time() * 1000)}"
    steps: list[FrontendContractSmokeStep] = []
    summary: dict[str, Any] = {}
    token: str | None = None

    def step(name: str, action: Callable[[], Any]) -> Any:
        try:
            value = action()
        except Exception as exc:
            steps.append(
                FrontendContractSmokeStep(
                    name=name,
                    ok=False,
                    error_message=str(exc),
                ),
            )
            raise
        steps.append(FrontendContractSmokeStep(name=name, ok=True))
        return value

    try:
        option_checks = step("options_metadata", lambda: _check_options(client))
        summary["option_checks"] = option_checks

        auth = step(
            "telegram_auth",
            lambda: _check_telegram_auth(client, effective_tg_user_id),
        )
        token = auth["token"]
        auth_account = auth["account"]
        account_id = auth_account["id"]
        summary["account_id"] = account_id
        summary["auth_account_credits"] = auth_account["credits"]
        summary["auth_account_public_name"] = auth_account["public_name"]
        summary["auth_account_has_avatar_key"] = "avatar" in auth_account

        language, cfg_summary = step(
            "account_language_config",
            lambda: _check_account_language_config(client, token, account_id),
        )
        summary["language_id"] = language["id"]
        summary.update(cfg_summary)

        book, first_chapter, second_chapter, book_summary = step(
            "book_chapter_contract",
            lambda: _check_book_chapter_contract(
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
        summary.update(book_summary)
        summary["first_chapter_id"] = first_chapter["id"]
        summary["chapter_render_book_id"] = first_chapter["book"]["id"]
        summary["chapter_render_book_name"] = first_chapter["book"]["name"]
        summary["chapter_render_book_language_id"] = first_chapter["book"]["language_id"]
        summary["chapter_render_book_chapter_count"] = len(first_chapter["book"]["chapters"])
        summary["chapter_render_content_count"] = len(first_chapter["content"])
        summary["chapter_render_first_token"] = first_chapter["content"][0]["name"]
        summary["chapter_render_first_word_id"] = first_chapter["content"][0]["w"]
        summary["chapter_render_first_position"] = first_chapter["content"][0]["p"]
        summary["second_chapter_id"] = second_chapter["id"]

        text_part, generic_text_part, phrase, generic_phrase = step(
            "text_phrase_contract",
            lambda: _check_text_phrase_contract(client, token, first_chapter),
        )
        summary["text_part_id"] = text_part["id"]
        summary["generic_text_part_id"] = generic_text_part["id"]
        summary["phrase_id"] = phrase["id"]
        summary["generic_phrase_id"] = generic_phrase["id"]

        study, transactions = step(
            "study_transaction_referral_contract",
            lambda: _check_study_transaction_referral_contract(
                client,
                token,
                first_chapter,
                text_part,
                phrase,
            ),
        )
        summary["study_id"] = study["id"]
        summary["study_detail_count"] = transactions["study_detail_count"]
        summary["study_detail_word_id"] = transactions["study_detail_word_id"]
        summary["study_detail_text_part_id"] = transactions["study_detail_text_part_id"]
        summary["study_detail_phrase_id"] = transactions["study_detail_phrase_id"]
        summary["study_list_render_count"] = transactions["study_list_render_count"]
        summary["study_list_first_type"] = transactions["study_list_first_type"]
        summary["study_list_first_name"] = transactions["study_list_first_name"]
        summary["study_list_first_translate"] = transactions[
            "study_list_first_translate"
        ]
        summary["study_list_first_success_logs"] = transactions[
            "study_list_first_success_logs"
        ]
        summary["transaction_count"] = transactions["transaction_count"]
        summary["usage_transaction_count"] = transactions["usage_transaction_count"]
        summary["bill_id"] = transactions["bill_id"]
        summary["transaction_sample_type"] = transactions["transaction_sample_type"]
        summary["transaction_sample_value"] = transactions["transaction_sample_value"]
        summary["referral_url"] = transactions["referral_url"]
        summary["referral_percentage"] = transactions["referral_percentage"]
        summary["referrals_count"] = transactions["referrals_count"]
        summary["referral_first_full_name"] = transactions["referral_first_full_name"]
        summary["referral_first_earned_amount"] = transactions[
            "referral_first_earned_amount"
        ]
        summary["referral_first_has_avatar_key"] = transactions[
            "referral_first_has_avatar_key"
        ]
        summary["referral_first_create_time"] = transactions[
            "referral_first_create_time"
        ]

        delete_summary = step(
            "delete_contract",
            lambda: _check_delete_contract(
                client,
                token,
                book["id"],
                second_chapter["id"],
                generic_text_part["id"],
                generic_phrase["id"],
                language["id"],
                effective_seed,
            ),
        )
        summary.update(delete_summary)
    except Exception as exc:
        return FrontendContractSmokeResult(
            ok=False,
            api_root=api_root.rstrip("/"),
            tg_user_id=effective_tg_user_id,
            steps=tuple(steps),
            summary=summary,
            error_message=str(exc),
        )

    return FrontendContractSmokeResult(
        ok=True,
        api_root=api_root.rstrip("/"),
        tg_user_id=effective_tg_user_id,
        steps=tuple(steps),
        summary=summary,
    )


def _check_options(client: JsonHttpClient) -> list[str]:
    resources = [
        "book",
        "chapter",
        "language",
        "phrase",
        "study_phrase",
        "text_part",
        "transaction",
        "word",
    ]
    for resource in resources:
        options = client.request("OPTIONS", f"/{resource}/").data
        _require(
            isinstance(options, dict) and bool(options.get("actions")),
            f"OPTIONS /{resource}/ did not return actions: {options}",
        )
    return resources


def _check_telegram_auth(
    client: JsonHttpClient,
    tg_user_id: int,
) -> dict[str, Any]:
    auth = client.request(
        "POST",
        "/account/telegram_auth/",
        body={
            "auth_data": {
                "user": {
                    "id": tg_user_id,
                    "first_name": "Contract",
                    "last_name": "Smoke",
                    "username": f"contract_smoke_{tg_user_id}",
                    "language_code": "en",
                },
            },
        },
    ).data
    _require(auth.get("token"), f"telegram_auth did not return token: {auth}")
    _require(
        auth.get("account", {}).get("id"),
        f"telegram_auth did not return account: {auth}",
    )
    _require_account_render_shape(auth["account"], "account/telegram_auth")
    return auth


def _check_account_language_config(
    client: JsonHttpClient,
    token: str,
    account_id: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    loaded_before = client.request("GET", "/account/load/", token=token).data
    _require(
        loaded_before.get("id") == account_id,
        f"account/load returned a different account: {loaded_before}",
    )
    _require_account_render_shape(loaded_before, "account/load before patch")

    languages = client.request("GET", "/language/", token=token).data
    language = _first_item(languages)
    _require(language.get("id"), f"No language in /language/: {languages}")
    _require_language_render_shape(language, "language list item")
    language_detail = client.request(
        "GET",
        f"/language/{language['id']}/",
        token=token,
    ).data
    _require(
        language_detail.get("id") == language["id"],
        f"language detail returned wrong id: {language_detail}",
    )
    _require_language_render_shape(language_detail, "language detail")

    image_group = client.request(
        "PATCH",
        "/language/update_image_group/",
        token=token,
        body={"id": language["id"], "slug": "contract"},
    ).data
    _require(
        image_group.get("updated") is True and image_group.get("id") == language["id"],
        f"language image group hook did not echo update: {image_group}",
    )

    patched = client.request(
        "PATCH",
        "/account/profile/",
        token=token,
        body={
            "language_id": language["id"],
            "ai_type": "local",
            "use_google_translate": False,
            "public_name": "Contract Smoke User",
        },
    ).data
    _require(
        patched.get("language_id") == language["id"]
        and patched.get("ai_type") == "local"
        and patched.get("use_google_translate") is False
        and patched.get("public_name") == "Contract Smoke User",
        f"account/profile settings were not preserved: {patched}",
    )
    _require_account_render_shape(patched, "account/profile patch")
    loaded_after = client.request("GET", "/account/load/", token=token).data
    _require(
        loaded_after.get("language_id") == language["id"]
        and loaded_after.get("ai_type") == "local"
        and loaded_after.get("use_google_translate") is False
        and loaded_after.get("public_name") == "Contract Smoke User",
        f"account/load lost profile setting: {loaded_after}",
    )
    _require_account_render_shape(loaded_after, "account/load after patch")
    link_preview = client.request(
        "POST",
        "/account/send_link_to_tg/",
        token=token,
        body={
            "text": "Open this Lazy Reader section",
            "path": "/books/22/",
            "dry_run": True,
        },
    ).data
    _require(
        link_preview.get("success") is True
        and link_preview.get("dry_run") is True
        and str(link_preview.get("web_app_url") or "").endswith("/books/22/")
        and isinstance(link_preview.get("keyboard"), list),
        f"account/send_link_to_tg dry-run contract failed: {link_preview}",
    )

    cfg = client.request("GET", "/book/load_cfg/", token=token).data
    _require(
        isinstance(cfg.get("stars_credits"), int | float)
        and isinstance(cfg.get("credits_referral_percentage"), int)
        and isinstance(cfg.get("ai_types"), list)
        and cfg["ai_types"]
        and isinstance(cfg.get("transaction_types"), list)
        and cfg["transaction_types"]
        and isinstance(cfg.get("language_levels"), dict)
        and cfg["language_levels"]
        and isinstance(cfg.get("ai_chapter_types"), dict)
        and cfg["ai_chapter_types"],
        f"Invalid book/load_cfg: {cfg}",
    )
    first_ai_type = cfg["ai_types"][0]
    _require(
        isinstance(first_ai_type, dict)
        and isinstance(first_ai_type.get("id"), str)
        and isinstance(first_ai_type.get("name"), str),
        f"book/load_cfg ai_types must be autocomplete-ready objects: {cfg}",
    )
    article = client.request(
        "POST",
        "/book/parse_article/",
        token=token,
        body={"url": "https://example.test/article"},
    ).data
    _require(
        article.get("disabled") is True and article.get("url"),
        f"parse_article disabled contract changed: {article}",
    )
    subtitles = client.request(
        "POST",
        "/book/parse_subtitles/",
        token=token,
        body={"url": "https://example.test/subs"},
    ).data
    _require(
        subtitles.get("disabled") is True,
        f"parse_subtitles disabled contract changed: {subtitles}",
    )
    return language, {
        "account_credits": loaded_after["credits"],
        "account_language_id": loaded_after["language_id"],
        "account_ai_type": loaded_after["ai_type"],
        "account_use_google_translate": loaded_after["use_google_translate"],
        "account_public_name": loaded_after["public_name"],
        "account_full_name": loaded_after["full_name"],
        "account_has_avatar_key": "avatar" in loaded_after,
        "language_render_slug": language["slug"],
        "language_render_name": language["name"],
        "language_render_original_name": language["original_name"],
        "cfg_first_ai_type_id": first_ai_type["id"],
        "cfg_first_ai_type_name": first_ai_type["name"],
        "cfg_stars_credits": cfg["stars_credits"],
        "cfg_referral_percentage": cfg["credits_referral_percentage"],
        "cfg_ai_type_count": len(cfg["ai_types"]),
        "cfg_transaction_type_count": len(cfg["transaction_types"]),
        "cfg_language_level_count": len(cfg["language_levels"]),
        "cfg_ai_chapter_type_count": len(cfg["ai_chapter_types"]),
    }


def _require_language_render_shape(language: dict[str, Any], label: str) -> None:
    _require(
        language.get("id")
        and isinstance(language.get("slug"), str)
        and bool(language.get("slug"))
        and isinstance(language.get("name"), str)
        and bool(language.get("name"))
        and isinstance(language.get("original_name"), str)
        and bool(language.get("original_name")),
        f"{label} is not renderable by language UI: {language}",
    )


def _require_account_render_shape(account: dict[str, Any], label: str) -> None:
    credits = account.get("credits")
    _require(
        isinstance(credits, int | float) and not isinstance(credits, bool),
        f"{label} must expose numeric credits for header: {account}",
    )
    _require(
        "language_id" in account
        and "ai_type" in account
        and "use_google_translate" in account,
        f"{label} must expose language and AI settings: {account}",
    )
    _require(
        "public_name" in account and "full_name" in account,
        f"{label} must expose display names: {account}",
    )
    _require("avatar" in account, f"{label} must expose avatar key: {account}")


def _check_book_chapter_contract(
    client: JsonHttpClient,
    token: str,
    language_id: int,
    seed: str,
    chapter_ready_attempts: int,
    chapter_ready_delay_seconds: float,
    sleep: Callable[[float], object],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    book = client.request(
        "POST",
        "/book/",
        token=token,
        body={
            "name": f"Contract Book {seed}",
            "language_id": language_id,
            "description": "Contract smoke description",
            "image": CONTRACT_BOOK_IMAGE,
        },
    ).data
    _require(
        book.get("id") and book.get("description") == "Contract smoke description",
        f"book create contract failed: {book}",
    )
    _require(
        str(book.get("image") or "").startswith("/uploads/")
        and str(book.get("croped_image") or "").startswith("/uploads/"),
        f"book create image upload contract failed: {book}",
    )
    book_list = client.request("GET", "/book/", token=token).data
    book_list_item = next(
        (item for item in _items(book_list) if item.get("id") == book["id"]),
        None,
    )
    _require(
        book_list_item is not None,
        f"book list misses created book: {book_list}",
    )
    _require_book_card_render_shape(
        book_list_item,
        language_id=language_id,
        label="book list item",
    )
    book_detail = client.request("GET", f"/book/{book['id']}/", token=token).data
    _require(
        book_detail.get("chapters_count") == 0,
        f"new book should have zero chapters: {book_detail}",
    )
    _require_book_page_render_shape(
        book_detail,
        language_id=language_id,
        expected_chapter_count=0,
        label="new book detail",
    )
    book_patch = client.request(
        "PATCH",
        f"/book/{book['id']}/",
        token=token,
        body={
            "name": f"{book['name']} Patched",
            "language_id": language_id,
            "description": "Contract smoke description patched",
            "image": CONTRACT_BOOK_PATCH_IMAGE,
            "is_active": True,
        },
    ).data
    _require(
        str(book_patch.get("name", "")).endswith("Patched")
        and book_patch.get("is_active") is True,
        f"book patch contract failed: {book_patch}",
    )
    _require_book_page_render_shape(
        book_patch,
        language_id=language_id,
        expected_chapter_count=0,
        label="book patch",
    )

    first_created = client.request(
        "POST",
        f"/book/{book['id']}/add_chapter/",
        token=token,
        body={
            "name": "Contract First",
            "chapter_type": "articles",
            "chapter_input": {
                "text": (
                    "alpha beta gamma delta epsilon zeta eta theta iota kappa "
                    "lambda mu nu xi omicron pi rho sigma tau"
                ),
            },
        },
    ).data
    first_chapter_id = _first_item(first_created.get("chapters") or {}).get("id")
    _require(first_chapter_id, f"First chapter create failed: {first_created}")

    second_created = client.request(
        "POST",
        f"/book/{book['id']}/add_chapter/",
        token=token,
        body={
            "name": "Contract Second",
            "chapter_type": "articles",
            "chapter_input": {
                "text": (
                    "reader workers create chapters asynchronously while frontend "
                    "reducers keep polling for readiness and order"
                ),
            },
        },
    ).data
    second_chapter_id = next(
        (
            item.get("id")
            for item in second_created.get("chapters", [])
            if item.get("id") != first_chapter_id
        ),
        None,
    )
    _require(second_chapter_id, f"Second chapter create failed: {second_created}")

    first_chapter = _wait_for_ready_chapter(
        client,
        token,
        int(first_chapter_id),
        chapter_ready_attempts,
        chapter_ready_delay_seconds,
        12,
        sleep,
    )
    _require_chapter_page_render_shape(
        first_chapter,
        book_id=book["id"],
        language_id=language_id,
        minimum_content_count=12,
        label="first chapter detail",
    )
    second_chapter = _wait_for_ready_chapter(
        client,
        token,
        int(second_chapter_id),
        chapter_ready_attempts,
        chapter_ready_delay_seconds,
        8,
        sleep,
    )
    _require_chapter_page_render_shape(
        second_chapter,
        book_id=book["id"],
        language_id=language_id,
        minimum_content_count=8,
        label="second chapter detail",
    )
    chapter_list = client.request("GET", "/chapter/", token=token).data
    _require(
        any(item.get("id") == first_chapter_id for item in _items(chapter_list)),
        f"chapter list misses created chapter: {chapter_list}",
    )
    renamed = client.request(
        "PATCH",
        f"/chapter/{first_chapter_id}/",
        token=token,
        body={"name": "Contract First Renamed"},
    ).data
    _require(
        renamed.get("name") == "Contract First Renamed",
        f"chapter patch contract failed: {renamed}",
    )
    percent = client.request(
        "POST",
        f"/chapter/{first_chapter_id}/set_percent/",
        token=token,
        body={"percent": 73},
    ).data
    _require(percent.get("percent") == 73, f"chapter set_percent failed: {percent}")
    sorted_book = client.request(
        "POST",
        f"/book/{book['id']}/sort_chapters/",
        token=token,
        body={"ordering": [second_chapter_id, first_chapter_id]},
    ).data
    _require(
        _first_item(sorted_book.get("chapters") or {}).get("id") == second_chapter_id,
        f"sort_chapters did not reorder serialized chapters: {sorted_book}",
    )
    _require_book_page_render_shape(
        sorted_book,
        language_id=language_id,
        expected_chapter_count=2,
        label="sorted book page",
    )
    sorted_first_chapter = _first_item(sorted_book["chapters"])
    return book, first_chapter, second_chapter, {
        "book_create_render_image": book["image"],
        "book_list_render_image": book_list_item["image"],
        "book_list_render_language_id": book_list_item["language_id"],
        "book_list_render_chapters_count": len(book_list_item["chapters"]),
        "book_list_render_ready_percent": book_list_item["ready_percent"],
        "book_patch_render_description": book_patch["description"],
        "book_patch_render_image": book_patch["image"],
        "book_page_chapter_count": len(sorted_book["chapters"]),
        "book_page_first_chapter_percent": sorted_first_chapter["percent"],
        "first_chapter_payload_type": "articles",
        "second_chapter_payload_type": "articles",
    }


def _require_book_card_render_shape(
    book: dict[str, Any],
    *,
    language_id: int,
    label: str,
) -> None:
    _require(book.get("image"), f"{label} must expose image for card: {book}")
    _require(
        book.get("language_id") == language_id,
        f"{label} must expose language_id for slug: {book}",
    )
    _require(
        isinstance(book.get("chapters"), list),
        f"{label} must expose chapters list for count: {book}",
    )
    _require(
        isinstance(book.get("is_book_ready"), bool),
        f"{label} must expose is_book_ready: {book}",
    )
    _require(
        isinstance(book.get("ready_percent"), int | float),
        f"{label} must expose numeric ready_percent: {book}",
    )


def _require_book_page_render_shape(
    book: dict[str, Any],
    *,
    language_id: int,
    expected_chapter_count: int,
    label: str,
) -> None:
    _require_book_card_render_shape(book, language_id=language_id, label=label)
    _require(
        book.get("chapters_count") == expected_chapter_count,
        f"{label} chapters_count mismatch: {book}",
    )
    chapters = book.get("chapters")
    _require(
        isinstance(chapters, list) and len(chapters) == expected_chapter_count,
        f"{label} must expose chapter objects list: {book}",
    )
    for chapter in chapters:
        _require(
            chapter.get("id")
            and chapter.get("name")
            and isinstance(chapter.get("is_ready"), bool)
            and isinstance(chapter.get("percent"), int | float),
            f"{label} chapter is not renderable: {chapter}",
        )


def _require_chapter_page_render_shape(
    chapter: dict[str, Any],
    *,
    book_id: int,
    language_id: int,
    minimum_content_count: int,
    label: str,
) -> None:
    book = chapter.get("book")
    _require(
        isinstance(book, dict)
        and book.get("id") == book_id
        and book.get("name")
        and book.get("language_id") == language_id
        and isinstance(book.get("chapters"), list),
        f"{label} must expose renderable book header/navigation: {chapter}",
    )
    content = chapter.get("content")
    _require(
        isinstance(content, list) and len(content) >= minimum_content_count,
        f"{label} must expose chapter content tokens: {chapter}",
    )
    first_token = content[0]
    for token_field in ("id", "name", "position", "p", "n", "w"):
        _require(
            token_field in first_token,
            f"{label} first content token misses {token_field}: {first_token}",
        )
    _require(
        isinstance(chapter.get("percent"), int | float),
        f"{label} must expose numeric percent: {chapter}",
    )


def _check_text_phrase_contract(
    client: JsonHttpClient,
    token: str,
    chapter: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    word_indexes = [
        item["id"]
        for item in chapter.get("content", [])
        if item.get("w") and item.get("id")
    ][:4]
    _require(len(word_indexes) >= 4, f"not enough word tokens: {chapter}")

    text_part = client.request(
        "POST",
        "/text_part/create_from_indexes/",
        token=token,
        body={"indexes": word_indexes, "action": "translate"},
    ).data
    _require(
        text_part.get("id") and text_part.get("translate", {}).get("translate"),
        f"text_part/create_from_indexes contract failed: {text_part}",
    )
    text_part_detail = client.request(
        "GET",
        f"/text_part/{text_part['id']}/",
        token=token,
    ).data
    _require(
        text_part_detail.get("id") == text_part["id"]
        and text_part_detail.get("translate", {}).get("translate")
        and text_part_detail.get("words"),
        f"text_part detail contract failed: {text_part_detail}",
    )
    text_part = text_part_detail
    generic_text_part = client.request(
        "POST",
        "/text_part/",
        token=token,
        body={
            "chapter": chapter["id"],
            "name": "generic text part",
            "translate": {
                "translate": "generic translation",
                "description": "generic note",
            },
        },
    ).data
    _require(generic_text_part.get("id"), f"generic text_part failed: {generic_text_part}")
    text_part_list = client.request(
        "GET",
        f"/text_part/?chapter={chapter['id']}",
        token=token,
    ).data
    _require(
        any(item.get("id") == text_part["id"] for item in _items(text_part_list)),
        f"text_part list misses created item: {text_part_list}",
    )
    text_part_patch = client.request(
        "PATCH",
        f"/text_part/{generic_text_part['id']}/",
        token=token,
        body={"description": "patched note"},
    ).data
    _require(
        text_part_patch.get("translate", {}).get("description") == "patched note",
        f"text_part patch contract failed: {text_part_patch}",
    )

    phrase = client.request(
        "POST",
        "/phrase/create_from_indexes/",
        token=token,
        body={"indexes_list": [word_indexes[1:4]]},
    ).data
    phrase = _first_item(phrase)
    _require(phrase.get("id"), f"phrase/create_from_indexes failed: {phrase}")
    phrase_detail = client.request(
        "GET",
        f"/phrase/{phrase['id']}/",
        token=token,
    ).data
    _require(
        phrase_detail.get("id") == phrase["id"]
        and phrase_detail.get("translate", {}).get("translate")
        and phrase_detail.get("words")
        and phrase_detail.get("text_part") == text_part["id"],
        f"phrase detail contract failed: {phrase_detail}",
    )
    phrase = phrase_detail
    generic_phrase = client.request(
        "POST",
        "/phrase/",
        token=token,
        body={
            "chapter": chapter["id"],
            "name": "generic phrase",
            "translate": {
                "translate": "generic phrase translation",
                "description": "generic phrase note",
            },
            "text_part": text_part["id"],
        },
    ).data
    _require(generic_phrase.get("id"), f"generic phrase failed: {generic_phrase}")
    phrase_list = client.request("GET", "/phrase/", token=token).data
    _require(
        any(item.get("id") == phrase["id"] for item in _items(phrase_list)),
        f"phrase list misses created item: {phrase_list}",
    )
    phrases_for_text_part = client.request(
        "GET",
        f"/phrase/load_for_text_part/?text_part={text_part['id']}",
        token=token,
    ).data
    _require(
        any(item.get("id") == generic_phrase["id"] for item in _items(phrases_for_text_part)),
        f"phrase/load_for_text_part misses generic phrase: {phrases_for_text_part}",
    )
    study_phrases = client.request(
        "GET",
        "/phrase/get_study_phrases/",
        token=token,
    ).data
    _require(
        isinstance(study_phrases, list),
        f"phrase/get_study_phrases did not return an array: {study_phrases}",
    )
    phrase_patch = client.request(
        "PATCH",
        f"/phrase/{generic_phrase['id']}/",
        token=token,
        body={"description": "patched phrase note"},
    ).data
    _require(
        phrase_patch.get("translate", {}).get("description") == "patched phrase note",
        f"phrase patch contract failed: {phrase_patch}",
    )
    return text_part, generic_text_part, phrase, generic_phrase


def _check_study_transaction_referral_contract(
    client: JsonHttpClient,
    token: str,
    chapter: dict[str, Any],
    text_part: dict[str, Any],
    phrase: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, int]]:
    word_id = next(
        (item.get("w") for item in chapter.get("content", []) if item.get("w")),
        None,
    )
    _require(word_id, f"chapter has no word id: {chapter}")
    study_targets = (
        ("word_id", word_id),
        ("text_part_id", text_part["id"]),
        ("phrase_id", phrase["id"]),
    )
    studies: list[dict[str, Any]] = []
    for field, value in study_targets:
        study = client.request(
            "POST",
            "/study_phrase/",
            token=token,
            body={
                "is_active": True,
                "chapter_id": chapter["id"],
                field: value,
            },
        ).data
        _require(
            study.get("id") and study.get(field) in {value, None},
            f"study_phrase create {field} contract failed: {study}",
        )
        studies.append(study)
    study = studies[0]
    _require(study.get("id"), f"study_phrase create contract failed: {study}")
    study_list = client.request("GET", "/study_phrase/", token=token).data
    _require(
        all(
            any(item.get("id") == study_item["id"] for item in _items(study_list))
            for study_item in studies
        ),
        f"study_phrase list misses created item: {study_list}",
    )
    study_list_render = _require_study_list_render_shape(
        study_list,
        expected_ids=[study_item["id"] for study_item in studies],
    )
    study_details: dict[str, dict[str, Any]] = {}
    for field, value in study_targets:
        detail = client.request(
            "GET",
            f"/study_phrase/{expected_study_id_for_field(studies, study_targets, field)}/",
            token=token,
        ).data
        _require_study_detail_shape(
            detail,
            field=field,
            target_id=value,
            chapter_id=chapter["id"],
        )
        study_details[field] = detail
    study_patch = client.request(
        "PATCH",
        f"/study_phrase/{study['id']}/",
        token=token,
        body={"is_active": False, "chapter_id": chapter["id"]},
    ).data
    _require(
        study_patch.get("is_active") is False
        and study_patch.get("chapter_id") == chapter["id"],
        f"study_phrase patch contract failed: {study_patch}",
    )
    expected_checks = {
        field: {
            "target_id": value,
            "study_id": studies[index]["id"],
            "is_active": False if index == 0 else True,
        }
        for index, (field, value) in enumerate(study_targets)
    }
    for field, value in study_targets:
        study_check = client.request(
            "GET",
            f"/study_phrase/check_exist/?{field}={value}",
            token=token,
        ).data
        check_mapping = study_check[1] if isinstance(study_check, list) else None
        expected = expected_checks[field]
        actual = (
            check_mapping.get(expected["target_id"])
            or check_mapping.get(str(expected["target_id"]))
            if isinstance(check_mapping, dict)
            else None
        )
        _require(
            isinstance(study_check, list)
            and len(study_check) == 2
            and study_check[0] == field,
            f"study_phrase/check_exist {field} contract failed: {study_check}",
        )
        _require(
            isinstance(actual, list)
            and len(actual) >= 2
            and actual[0] == expected["study_id"]
            and actual[1] is expected["is_active"],
            f"study_phrase/check_exist {field} mapping mismatch: {study_check}",
        )

    batch_word_id = next(
        (
            item.get("w")
            for item in chapter.get("content", [])
            if item.get("w") and item.get("w") != word_id
        ),
        None,
    )
    _require(batch_word_id, f"chapter has no second word id: {chapter}")
    batch_check = client.request(
        "GET",
        f"/study_phrase/check_exist/?word_id={word_id},{batch_word_id}",
        token=token,
    ).data
    batch_mapping = batch_check[1] if isinstance(batch_check, list) else None
    studied_actual = (
        batch_mapping.get(word_id) or batch_mapping.get(str(word_id))
        if isinstance(batch_mapping, dict)
        else None
    )
    unstudied_actual = (
        batch_mapping.get(batch_word_id) or batch_mapping.get(str(batch_word_id))
        if isinstance(batch_mapping, dict)
        else None
    )
    _require(
        isinstance(batch_check, list)
        and len(batch_check) == 2
        and batch_check[0] == "word_id"
        and isinstance(studied_actual, list)
        and studied_actual[:2] == [studies[0]["id"], False]
        and isinstance(unstudied_actual, list)
        and unstudied_actual[:2] == [None, False],
        f"study_phrase/check_exist word_id batch contract failed: {batch_check}",
    )

    transaction_list = client.request("GET", "/transaction/", token=token).data
    transaction_item = _first_item(transaction_list)
    _require(
        isinstance(transaction_list.get("count"), int)
        and transaction_item.get("id")
        and transaction_item.get("create_time")
        and transaction_item.get("transaction_type")
        and isinstance(transaction_item.get("value"), int | float),
        f"transaction list contract failed: {transaction_list}",
    )
    usage_list = client.request(
        "GET",
        "/transaction/?transaction_type=ai_usage",
        token=token,
    ).data
    usage_item = _first_item(usage_list)
    _require(
        isinstance(usage_list.get("count"), int)
        and usage_item.get("transaction_type") == "ai_usage",
        f"transaction usage list contract failed: {usage_list}",
    )
    bill = client.request(
        "POST",
        "/transaction/send_tg_payment/",
        token=token,
        body={"cost": 17},
    ).data
    _require(
        bill.get("success") is True
        and bill.get("bill_id")
        and bill.get("invoice_payload") == str(bill["bill_id"]),
        f"transaction/send_tg_payment contract failed: {bill}",
    )
    referral_code = client.request(
        "GET",
        "/transaction/get_referral_code/",
        token=token,
    ).data
    referral_tg_user_id = 995000000 + int(chapter["id"])
    referral_start = client.request(
        "POST",
        "/telegram/update/",
        body={
            "update_id": 996000000 + int(chapter["id"]),
            "message": {
                "message_id": 1,
                "date": 1,
                "chat": {"id": referral_tg_user_id, "type": "private"},
                "from": {
                    "id": referral_tg_user_id,
                    "is_bot": False,
                    "first_name": "Referral",
                    "last_name": "Friend",
                    "username": f"ref_friend_{referral_tg_user_id}",
                    "language_code": "en",
                },
                "text": f"/start ref_{referral_code.get('code')}",
            },
        },
    ).data
    _require(
        referral_start.get("success") is True,
        f"telegram referral start failed: {referral_start}",
    )
    referrals = client.request(
        "GET",
        "/transaction/get_referrals/",
        token=token,
    ).data
    referral_render = _require_referral_list_render_shape(referrals)
    _require(
        bool(referral_code.get("code"))
        and bool(referral_code.get("referral_url"))
        and isinstance(referral_code.get("percentage"), int)
        and isinstance(referrals, list),
        f"referral contract failed: code={referral_code}, referrals={referrals}",
    )
    return study, {
        "study_detail_count": len(study_details),
        "study_detail_word_id": study_details["word_id"]["word"]["id"],
        "study_detail_text_part_id": study_details["text_part_id"]["text_part"]["id"],
        "study_detail_phrase_id": study_details["phrase_id"]["phrase"]["id"],
        **study_list_render,
        "transaction_count": transaction_list["count"],
        "usage_transaction_count": usage_list["count"],
        "bill_id": bill["bill_id"],
        "transaction_sample_type": transaction_item["transaction_type"],
        "transaction_sample_value": transaction_item["value"],
        "referral_url": referral_code["referral_url"],
        "referral_percentage": referral_code["percentage"],
        **referral_render,
    }


def _require_referral_list_render_shape(referrals: list[dict[str, Any]]) -> dict[str, Any]:
    _require(referrals, f"referral list must include a renderable item: {referrals}")
    first_referral = referrals[0]
    referred_account = first_referral.get("referral")
    _require(
        isinstance(referred_account, dict)
        and isinstance(referred_account.get("full_name"), str)
        and "avatar" in referred_account
        and isinstance(first_referral.get("earned_amount"), int | float)
        and isinstance(first_referral.get("create_time"), str),
        f"referral list item is not renderable: {first_referral}",
    )
    return {
        "referrals_count": len(referrals),
        "referral_first_full_name": referred_account["full_name"],
        "referral_first_earned_amount": first_referral["earned_amount"],
        "referral_first_has_avatar_key": "avatar" in referred_account,
        "referral_first_create_time": first_referral["create_time"],
    }


def expected_study_id_for_field(
    studies: Sequence[dict[str, Any]],
    study_targets: Sequence[tuple[str, int]],
    field: str,
) -> int:
    for index, (candidate_field, _) in enumerate(study_targets):
        if candidate_field == field:
            return studies[index]["id"]
    raise AssertionError(f"Missing study target field: {field}")


def _require_study_detail_shape(
    detail: dict[str, Any],
    *,
    field: str,
    target_id: int,
    chapter_id: int,
) -> None:
    _require(
        detail.get("id") and detail.get("chapter_id") == chapter_id,
        f"study_phrase detail must expose id and chapter_id: {detail}",
    )
    for score_field in (
        "audio_average",
        "forward_average",
        "reverse_average",
        "average",
    ):
        _require(
            isinstance(detail.get(score_field), int | float),
            f"study_phrase detail score {score_field} must be numeric: {detail}",
        )
    _require(
        isinstance(detail.get("success_logs"), int),
        f"study_phrase detail success_logs must be int: {detail}",
    )

    nested_key = field.removesuffix("_id")
    nested = detail.get(nested_key)
    _require(
        isinstance(nested, dict) and nested.get("id") == target_id,
        f"study_phrase detail misses nested {nested_key}: {detail}",
    )
    _require(
        nested.get("name") and isinstance(nested.get("translate"), dict),
        f"study_phrase detail nested {nested_key} must be renderable: {detail}",
    )


def _require_study_list_render_shape(
    study_list: Any,
    *,
    expected_ids: Sequence[int],
) -> dict[str, Any]:
    items = _items(study_list)
    _require(
        all(any(item.get("id") == expected_id for item in items) for expected_id in expected_ids),
        f"study_phrase list misses expected ids {expected_ids}: {study_list}",
    )
    render_items = [item for item in items if item.get("id") in set(expected_ids)]
    _require(render_items, f"study_phrase list has no renderable items: {study_list}")

    for item in render_items:
        _require_study_item_render_shape(item)

    first_item = render_items[0]
    first_type, first_detail = _study_item_type_and_detail(first_item)
    return {
        "study_list_render_count": len(render_items),
        "study_list_first_type": first_type,
        "study_list_first_name": first_detail["name"],
        "study_list_first_translate": first_detail["translate"]["translate"],
        "study_list_first_success_logs": first_item["success_logs"],
    }


def _require_study_item_render_shape(item: dict[str, Any]) -> None:
    _require(item.get("id"), f"study_phrase list item misses id: {item}")
    for score_field in (
        "audio_average",
        "forward_average",
        "reverse_average",
        "average",
    ):
        _require(
            isinstance(item.get(score_field), int | float),
            f"study_phrase list item {score_field} must be numeric: {item}",
        )
    _require(
        isinstance(item.get("success_logs"), int),
        f"study_phrase list item success_logs must be int: {item}",
    )

    item_type, detail = _study_item_type_and_detail(item)
    _require(
        item_type in {"word", "text_part", "phrase"}
        and isinstance(detail.get("name"), str)
        and isinstance(detail.get("translate"), dict)
        and isinstance(detail["translate"].get("translate"), str),
        f"study_phrase list item nested detail is not renderable: {item}",
    )
    _require("ai_voice" in detail, f"study_phrase list item misses ai_voice: {item}")


def _study_item_type_and_detail(item: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    for item_type in ("word", "text_part", "phrase"):
        detail = item.get(item_type)
        if isinstance(detail, dict):
            return item_type, detail
    raise RuntimeError(f"study_phrase list item misses word/text_part/phrase: {item}")


def _check_delete_contract(
    client: JsonHttpClient,
    token: str,
    book_id: int,
    second_chapter_id: int,
    generic_text_part_id: int,
    generic_phrase_id: int,
    language_id: int,
    seed: str,
) -> dict[str, Any]:
    deleted_phrase = client.request(
        "DELETE",
        f"/phrase/{generic_phrase_id}/",
        token=token,
    ).data
    _require(
        deleted_phrase.get("id") == generic_phrase_id,
        f"phrase delete contract failed: {deleted_phrase}",
    )
    deleted_text_part = client.request(
        "DELETE",
        f"/text_part/{generic_text_part_id}/",
        token=token,
    ).data
    _require(
        deleted_text_part.get("id") == generic_text_part_id,
        f"text_part delete contract failed: {deleted_text_part}",
    )
    book_after_chapter_delete = client.request(
        "DELETE",
        f"/book/{book_id}/delete_chapter/?chapter={second_chapter_id}",
        token=token,
    ).data
    remaining_chapters = book_after_chapter_delete.get("chapters") or []
    _require(
        book_after_chapter_delete.get("chapters_count") == 1
        and all(item.get("id") != second_chapter_id for item in remaining_chapters),
        f"delete_chapter contract failed: {book_after_chapter_delete}",
    )

    temp_book = client.request(
        "POST",
        "/book/",
        token=token,
        body={"name": f"Contract Delete {seed}", "language": language_id},
    ).data
    deleted_book = client.request(
        "DELETE",
        f"/book/{temp_book['id']}/",
        token=token,
    ).data
    _require(
        deleted_book.get("id") == temp_book["id"],
        f"book delete contract failed: {deleted_book}",
    )
    return {
        "remaining_chapters_after_delete": [
            item.get("id") for item in remaining_chapters
        ],
        "deleted_book_id": deleted_book["id"],
    }


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


def _items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        results = value.get("results")
        if isinstance(results, list):
            return [item for item in results if isinstance(item, dict)]
    return []


def _require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)
