from __future__ import annotations

from typing import Any

from infrastructure.runtime.legacy_compat_smoke import HttpResponse


class FakeFrontendContractHttpClient:
    def __init__(
        self,
        *,
        parser_disabled: bool = True,
        wrong_check_exist_mapping: bool = False,
    ) -> None:
        self.parser_disabled = parser_disabled
        self.wrong_check_exist_mapping = wrong_check_exist_mapping
        self.calls: list[tuple[str, str, str | None]] = []
        self.request_bodies: list[tuple[str, str, dict[str, Any]]] = []
        self.book_name = "Contract Book"
        self.book_description = "Contract smoke description"
        self.book_image = "/uploads/book-cover.png"
        self.first_chapter_name = "Contract First"
        self.second_chapter_deleted = False
        self.generic_text_part_deleted = False
        self.generic_phrase_deleted = False
        self.account_language_id = 1
        self.account_ai_type = "local"
        self.account_use_google_translate = False
        self.account_public_name = "Contract Smoke User"
        self.account_full_name = "Contract Smoke User"
        self.account_avatar: str | None = None
        self.account_credits = 42.5
        self.referral_created = False

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        token: str | None = None,
        allow_statuses: tuple[int, ...] = (),
    ) -> HttpResponse:
        self.calls.append((method, path, token))
        body = body or {}
        self.request_bodies.append((method, path, dict(body)))
        if method == "OPTIONS" and path in {
            "/book/",
            "/chapter/",
            "/language/",
            "/phrase/",
            "/study_phrase/",
            "/text_part/",
            "/transaction/",
            "/word/",
        }:
            return HttpResponse(status=200, data={"actions": {"POST": {}}})
        if method == "POST" and path == "/account/telegram_auth/":
            return HttpResponse(
                status=200,
                data={"token": "frontend-secret-token", "account": self._account()},
            )
        if method == "GET" and path == "/account/load/":
            return HttpResponse(status=200, data=self._account())
        if method == "PATCH" and path == "/account/profile/":
            self.account_language_id = body.get("language_id", self.account_language_id)
            self.account_ai_type = body.get("ai_type", self.account_ai_type)
            self.account_use_google_translate = body.get(
                "use_google_translate",
                self.account_use_google_translate,
            )
            self.account_public_name = body.get(
                "public_name",
                self.account_public_name,
            )
            self.account_full_name = self.account_public_name
            return HttpResponse(status=200, data=self._account())
        if method == "POST" and path == "/account/send_link_to_tg/":
            return HttpResponse(
                status=200,
                data={
                    "detail": "Link sent successfully",
                    "success": True,
                    "dry_run": body.get("dry_run"),
                    "web_app_url": "https://lang-reader.ngrok.app/books/22/",
                    "keyboard": [
                        [
                            {
                                "text": "Open WebApp",
                                "web_app": "https://lang-reader.ngrok.app/books/22/",
                            },
                        ],
                    ],
                },
            )
        if method == "GET" and path == "/language/":
            return HttpResponse(status=200, data=[self._language()])
        if method == "GET" and path == "/language/1/":
            return HttpResponse(status=200, data=self._language())
        if method == "PATCH" and path == "/language/update_image_group/":
            return HttpResponse(status=200, data={"updated": True, "id": body["id"]})
        if method == "GET" and path == "/book/load_cfg/":
            return HttpResponse(
                status=200,
                data={
                    "stars_credits": 1,
                    "credits_referral_percentage": 15,
                    "ai_types": [
                        {"id": "local", "name": "Local"},
                        {"id": "openai", "name": "OpenAI"},
                    ],
                    "transaction_types": [
                        ["start_bonus", "Start bonus"],
                        ["payment", "Payment"],
                        ["ai_usage", "AI usage"],
                    ],
                    "language_levels": {"a1": "A1", "b1": "B1"},
                    "ai_chapter_types": {"story": "Story", "dialog": "Dialog"},
                },
            )
        if method == "POST" and path == "/book/parse_article/":
            return HttpResponse(
                status=200,
                data={"disabled": self.parser_disabled, "url": body.get("url")},
            )
        if method == "POST" and path == "/book/parse_subtitles/":
            return HttpResponse(status=200, data={"disabled": self.parser_disabled})
        if method == "POST" and path == "/book/":
            if body.get("name", "").startswith("Contract Delete"):
                return HttpResponse(status=200, data={"id": 44, "name": body["name"]})
            if isinstance(body.get("image"), dict) and str(
                body["image"].get("content") or ""
            ).startswith("data:image/"):
                self.book_image = "/uploads/compat_books/contract-cover.png"
            return HttpResponse(
                status=200,
                data={
                    **self._book_render(22, self.book_name, []),
                    "description": body.get("description", self.book_description),
                },
            )
        if method == "GET" and path == "/book/":
            return HttpResponse(
                status=200,
                data={
                    "count": 1,
                    "results": [self._book_render(22, self.book_name, [])],
                },
            )
        if method == "GET" and path == "/book/22/":
            return HttpResponse(
                status=200,
                data=self._book_render(22, self.book_name, []),
            )
        if method == "PATCH" and path == "/book/22/":
            self.book_name = body["name"]
            self.book_description = body.get("description", self.book_description)
            if isinstance(body.get("image"), dict) and body["image"].get(
                "name"
            ) == "contract-cover-patched.png":
                self.book_image = "/uploads/compat_books/contract-cover-patched.png"
            return HttpResponse(
                status=200,
                data={
                    **self._book_render(22, self.book_name, []),
                    "is_active": body["is_active"],
                },
            )
        if method == "POST" and path == "/book/22/add_chapter/":
            if body["name"] == "Contract First":
                return HttpResponse(status=200, data={"chapters": [{"id": 31}]})
            return HttpResponse(status=200, data={"chapters": [{"id": 31}, {"id": 32}]})
        if method == "GET" and path == "/chapter/31/":
            return HttpResponse(status=200, data=self._chapter(31, self.first_chapter_name))
        if method == "GET" and path == "/chapter/32/":
            return HttpResponse(status=200, data=self._chapter(32, "Contract Second"))
        if method == "GET" and path == "/chapter/":
            return HttpResponse(status=200, data={"results": [{"id": 31}, {"id": 32}]})
        if method == "PATCH" and path == "/chapter/31/":
            self.first_chapter_name = body["name"]
            return HttpResponse(status=200, data={"id": 31, "name": self.first_chapter_name})
        if method == "POST" and path == "/chapter/31/set_percent/":
            return HttpResponse(status=200, data={"id": 31, "percent": body["percent"]})
        if method == "POST" and path == "/book/22/sort_chapters/":
            return HttpResponse(
                status=200,
                data=self._book_render(
                    22,
                    self.book_name,
                    [
                        self._book_chapter(32, "Contract Second"),
                        self._book_chapter(31, self.first_chapter_name),
                    ],
                ),
            )
        if method == "POST" and path == "/text_part/create_from_indexes/":
            return HttpResponse(
                status=200,
                data={"id": 51, "translate": {"translate": "translated text"}},
            )
        if method == "GET" and path == "/text_part/51/":
            return HttpResponse(
                status=200,
                data={
                    "id": 51,
                    "translate": {"translate": "translated text"},
                    "words": [{"id": 1, "word": {"id": 101}}],
                },
            )
        if method == "POST" and path == "/text_part/":
            return HttpResponse(
                status=200,
                data={"id": 52, "translate": {"description": "generic note"}},
            )
        if method == "GET" and path == "/text_part/?chapter=31":
            return HttpResponse(status=200, data=[{"id": 51}, {"id": 52}])
        if method == "PATCH" and path == "/text_part/52/":
            return HttpResponse(
                status=200,
                data={"id": 52, "translate": {"description": body["description"]}},
            )
        if method == "POST" and path == "/phrase/create_from_indexes/":
            return HttpResponse(status=200, data=[{"id": 61, "text_part": 51}])
        if method == "GET" and path == "/phrase/61/":
            return HttpResponse(
                status=200,
                data={
                    "id": 61,
                    "text_part": 51,
                    "translate": {"translate": "phrase translation"},
                    "words": [{"id": 2, "word": {"id": 102}}],
                },
            )
        if method == "POST" and path == "/phrase/":
            return HttpResponse(
                status=200,
                data={"id": 62, "translate": {"description": "generic phrase note"}},
            )
        if method == "GET" and path == "/phrase/":
            return HttpResponse(status=200, data=[{"id": 61}, {"id": 62}])
        if method == "GET" and path == "/phrase/load_for_text_part/?text_part=51":
            return HttpResponse(status=200, data=[{"id": 62}])
        if method == "GET" and path == "/phrase/get_study_phrases/":
            return HttpResponse(status=200, data=[])
        if method == "PATCH" and path == "/phrase/62/":
            return HttpResponse(
                status=200,
                data={"id": 62, "translate": {"description": body["description"]}},
            )
        if method == "POST" and path == "/study_phrase/":
            study_id = 71
            if "text_part_id" in body:
                study_id = 72
            if "phrase_id" in body:
                study_id = 73
            return HttpResponse(status=200, data={"id": study_id, **body})
        if method == "GET" and path == "/study_phrase/":
            return HttpResponse(
                status=200,
                data={
                    "results": [
                        self._study_detail(71, {"word": self._study_word_detail(101)}),
                        self._study_detail(72, {"text_part": self._text_part_detail(51)}),
                        self._study_detail(73, {"phrase": self._phrase_detail(61)}),
                    ]
                },
            )
        if method == "GET" and path == "/study_phrase/71/":
            return HttpResponse(
                status=200,
                data=self._study_detail(
                    71,
                    {"word": self._study_word_detail(101)},
                ),
            )
        if method == "GET" and path == "/study_phrase/72/":
            return HttpResponse(
                status=200,
                data=self._study_detail(
                    72,
                    {"text_part": self._text_part_detail(51)},
                ),
            )
        if method == "GET" and path == "/study_phrase/73/":
            return HttpResponse(
                status=200,
                data=self._study_detail(
                    73,
                    {"phrase": self._phrase_detail(61)},
                ),
            )
        if method == "PATCH" and path == "/study_phrase/71/":
            return HttpResponse(
                status=200,
                data={
                    "id": 71,
                    "is_active": body["is_active"],
                    "chapter_id": body["chapter_id"],
                },
            )
        if method == "GET" and path == "/study_phrase/check_exist/?word_id=101":
            return HttpResponse(status=200, data=["word_id", {101: [71, False]}])
        if method == "GET" and path == "/study_phrase/check_exist/?word_id=101,102":
            return HttpResponse(
                status=200,
                data=["word_id", {101: [71, False], 102: [None, False]}],
            )
        if method == "GET" and path == "/study_phrase/check_exist/?text_part_id=51":
            return HttpResponse(status=200, data=["text_part_id", {51: [72, True]}])
        if method == "GET" and path == "/study_phrase/check_exist/?phrase_id=61":
            if self.wrong_check_exist_mapping:
                return HttpResponse(status=200, data=["phrase_id", {61: [999, True]}])
            return HttpResponse(status=200, data=["phrase_id", {61: [73, True]}])
        if method == "GET" and path == "/transaction/":
            return HttpResponse(
                status=200,
                data={
                    "count": 2,
                    "results": [
                        {
                            "id": 91,
                            "create_time": "2026-07-07T12:00:00+00:00",
                            "transaction_type": "ai_usage",
                            "value": -3.5,
                        },
                    ],
                },
            )
        if method == "GET" and path == "/transaction/?transaction_type=ai_usage":
            return HttpResponse(
                status=200,
                data={
                    "count": 1,
                    "results": [
                        {
                            "id": 91,
                            "create_time": "2026-07-07T12:00:00+00:00",
                            "transaction_type": "ai_usage",
                            "value": -3.5,
                        },
                    ],
                },
            )
        if method == "POST" and path == "/transaction/send_tg_payment/":
            return HttpResponse(
                status=200,
                data={
                    "success": True,
                    "bill_id": 81,
                    "invoice_payload": "81",
                    "invoice_sent": False,
                },
            )
        if method == "GET" and path == "/transaction/get_referral_code/":
            return HttpResponse(
                status=200,
                data={
                    "code": "lr_11",
                    "percentage": 10,
                    "referral_url": "https://lang-reader.ngrok.app/?start=ref_lr_11",
                },
            )
        if method == "POST" and path == "/telegram/update/":
            self.referral_created = True
            return HttpResponse(
                status=200,
                data={
                    "success": True,
                    "handled": "start",
                    "account_id": 12,
                    "is_new": True,
                    "referral_added": True,
                },
            )
        if method == "GET" and path == "/transaction/get_referrals/":
            if not self.referral_created:
                return HttpResponse(status=200, data=[])
            return HttpResponse(
                status=200,
                data=[
                    {
                        "id": 1,
                        "referral": {
                            "id": 12,
                            "username": "TG:995000031:ref_friend_995000031",
                            "full_name": "Referral Friend",
                            "avatar": None,
                        },
                        "create_time": "2026-07-07T12:00:00+00:00",
                        "percentage": 15,
                        "earned_amount": 0,
                    }
                ],
            )
        if method == "DELETE" and path == "/phrase/62/":
            self.generic_phrase_deleted = True
            return HttpResponse(status=200, data={"id": 62})
        if method == "DELETE" and path == "/text_part/52/":
            self.generic_text_part_deleted = True
            return HttpResponse(status=200, data={"id": 52})
        if method == "DELETE" and path == "/book/22/delete_chapter/?chapter=32":
            self.second_chapter_deleted = True
            return HttpResponse(
                status=200,
                data={"id": 22, "chapters_count": 1, "chapters": [{"id": 31}]},
            )
        if method == "DELETE" and path == "/book/44/":
            return HttpResponse(status=200, data={"id": 44})
        raise AssertionError(f"Unexpected request: {method} {path}")

    def _book_render(
        self,
        book_id: int,
        name: str,
        chapters: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "id": book_id,
            "name": name,
            "description": self.book_description,
            "language": 1,
            "language_id": 1,
            "chapters_count": len(chapters),
            "image": self.book_image,
            "croped_image": self.book_image,
            "file": None,
            "is_active": True,
            "is_book_ready": all(chapter["is_ready"] for chapter in chapters),
            "ready_percent": 100,
            "chapters": chapters,
        }

    def _book_chapter(self, chapter_id: int, name: str) -> dict[str, Any]:
        return {
            "id": chapter_id,
            "name": name,
            "book": 22,
            "book_id": 22,
            "position": 0,
            "is_ready": True,
            "source_url": None,
            "percent": 0,
        }

    def _account(self) -> dict[str, Any]:
        return {
            "id": 11,
            "username": "contract_user",
            "email": None,
            "public_name": self.account_public_name,
            "full_name": self.account_full_name,
            "first_name": "Contract",
            "last_name": "User",
            "avatar": self.account_avatar,
            "credits": self.account_credits,
            "tg_user_id": 994123456,
            "tg_language_code": "en",
            "language_id": self.account_language_id,
            "ai_type": self.account_ai_type,
            "use_google_translate": self.account_use_google_translate,
            "is_active": True,
        }

    def _language(self) -> dict[str, Any]:
        return {
            "id": 1,
            "name": "English",
            "original_name": "English",
            "slug": "en",
        }

    def _study_detail(self, study_id: int, target: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": study_id,
            "is_active": True,
            "chapter": 31,
            "chapter_id": 31,
            "audio_average": 0.0,
            "forward_average": 1.0,
            "reverse_average": 2.0,
            "average": 1.5,
            "success_logs": 0,
            "create_time": "2026-07-07T12:00:00+00:00",
            **target,
        }

    def _study_word_detail(self, word_id: int) -> dict[str, Any]:
        return {
            "id": word_id,
            "name": "alpha",
            "translate": {"id": 201, "translate": "альфа"},
            "ai_voice": None,
        }

    def _text_part_detail(self, text_part_id: int) -> dict[str, Any]:
        return {
            "id": text_part_id,
            "name": "alpha beta gamma",
            "translate": {"translate": "translated text"},
            "ai_voice": None,
            "words": [self._study_word_detail(101)],
        }

    def _phrase_detail(self, phrase_id: int) -> dict[str, Any]:
        return {
            "id": phrase_id,
            "name": "alpha beta",
            "translate": {"translate": "translated phrase"},
            "text_part": {"id": 51},
            "ai_voice": None,
            "words": [self._study_word_detail(101)],
        }

    def _chapter(self, chapter_id: int, name: str) -> dict[str, Any]:
        return {
            "id": chapter_id,
            "name": name,
            "book": {
                "id": 22,
                "name": self.book_name,
                "language_id": 1,
                "chapters": [31, 32],
            },
            "book_id": 22,
            "position": 0,
            "is_ready": True,
            "source_url": None,
            "percent": 0,
            "content": [
                self._chapter_token(1, "alpha", 101, 0),
                self._chapter_token(2, "beta", 102, 1),
                self._chapter_token(3, "gamma", 103, 2),
                self._chapter_token(4, "delta", 104, 3),
                self._chapter_token(5, "epsilon", 105, 4),
                self._chapter_token(6, "zeta", 106, 5),
                self._chapter_token(7, "eta", 107, 6),
                self._chapter_token(8, "theta", 108, 7),
                self._chapter_token(9, "iota", 109, 8),
                self._chapter_token(10, "kappa", 110, 9),
                self._chapter_token(11, "lambda", 111, 10),
                self._chapter_token(12, "mu", 112, 11),
            ],
        }

    def _chapter_token(
        self, token_id: int, name: str, word_id: int, position: int
    ) -> dict[str, Any]:
        return {
            "id": token_id,
            "name": name,
            "position": position,
            "p": position,
            "n": 0,
            "w": word_id,
        }


def test_frontend_contract_smoke_runs_old_reducer_contract() -> None:
    from infrastructure.runtime.frontend_contract_smoke import (
        run_frontend_contract_smoke,
    )

    client = FakeFrontendContractHttpClient()

    result = run_frontend_contract_smoke(
        client=client,
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        tg_user_id=994123456,
        seed="test-seed",
        chapter_ready_attempts=1,
        sleep=lambda _: None,
    )

    assert result.ok is True
    assert result.summary["account_id"] == 11
    assert result.summary["auth_account_credits"] == 42.5
    assert result.summary["auth_account_public_name"] == "Contract Smoke User"
    assert result.summary["auth_account_has_avatar_key"] is True
    assert result.summary["account_credits"] == 42.5
    assert result.summary["account_language_id"] == 1
    assert result.summary["account_ai_type"] == "local"
    assert result.summary["account_use_google_translate"] is False
    assert result.summary["account_public_name"] == "Contract Smoke User"
    assert result.summary["account_full_name"] == "Contract Smoke User"
    assert result.summary["account_has_avatar_key"] is True
    assert result.summary["language_render_slug"] == "en"
    assert result.summary["language_render_name"] == "English"
    assert result.summary["language_render_original_name"] == "English"
    assert result.summary["cfg_first_ai_type_id"] == "local"
    assert result.summary["cfg_first_ai_type_name"] == "Local"
    assert result.summary["cfg_stars_credits"] == 1
    assert result.summary["cfg_referral_percentage"] == 15
    assert result.summary["cfg_ai_type_count"] == 2
    assert result.summary["cfg_transaction_type_count"] == 3
    assert result.summary["cfg_language_level_count"] == 2
    assert result.summary["cfg_ai_chapter_type_count"] == 2
    assert result.summary["book_id"] == 22
    assert result.summary["book_create_render_image"] == "/uploads/compat_books/contract-cover.png"
    assert result.summary["book_list_render_image"] == "/uploads/compat_books/contract-cover.png"
    assert result.summary["book_list_render_language_id"] == 1
    assert result.summary["book_list_render_chapters_count"] == 0
    assert result.summary["book_list_render_ready_percent"] == 100
    assert result.summary["book_patch_render_description"] == "Contract smoke description patched"
    assert result.summary["book_patch_render_image"] == "/uploads/compat_books/contract-cover-patched.png"
    assert result.summary["book_page_chapter_count"] == 2
    assert result.summary["book_page_first_chapter_percent"] == 0
    assert result.summary["first_chapter_id"] == 31
    assert result.summary["chapter_render_book_id"] == 22
    assert result.summary["chapter_render_book_name"] == "Contract Book Patched"
    assert result.summary["chapter_render_book_language_id"] == 1
    assert result.summary["chapter_render_book_chapter_count"] == 2
    assert result.summary["chapter_render_content_count"] == 12
    assert result.summary["chapter_render_first_token"] == "alpha"
    assert result.summary["chapter_render_first_word_id"] == 101
    assert result.summary["chapter_render_first_position"] == 0
    assert result.summary["first_chapter_payload_type"] == "articles"
    assert result.summary["second_chapter_payload_type"] == "articles"
    assert result.summary["second_chapter_id"] == 32
    assert result.summary["text_part_id"] == 51
    assert result.summary["phrase_id"] == 61
    assert result.summary["bill_id"] == 81
    assert result.summary["transaction_sample_type"] == "ai_usage"
    assert result.summary["transaction_sample_value"] == -3.5
    assert result.summary["referral_url"] == "https://lang-reader.ngrok.app/?start=ref_lr_11"
    assert result.summary["referral_percentage"] == 10
    assert result.summary["referrals_count"] == 1
    assert result.summary["referral_first_full_name"] == "Referral Friend"
    assert result.summary["referral_first_earned_amount"] == 0
    assert result.summary["referral_first_has_avatar_key"] is True
    assert result.summary["referral_first_create_time"] == "2026-07-07T12:00:00+00:00"
    assert result.summary["study_detail_count"] == 3
    assert result.summary["study_detail_word_id"] == 101
    assert result.summary["study_detail_text_part_id"] == 51
    assert result.summary["study_detail_phrase_id"] == 61
    assert result.summary["study_list_render_count"] == 3
    assert result.summary["study_list_first_type"] == "word"
    assert result.summary["study_list_first_name"] == "alpha"
    assert result.summary["study_list_first_translate"] == "альфа"
    assert result.summary["study_list_first_success_logs"] == 0
    assert ("GET", "/text_part/51/", "frontend-secret-token") in client.calls
    assert ("GET", "/phrase/61/", "frontend-secret-token") in client.calls
    assert ("GET", "/study_phrase/71/", "frontend-secret-token") in client.calls
    assert ("GET", "/study_phrase/72/", "frontend-secret-token") in client.calls
    assert ("GET", "/study_phrase/73/", "frontend-secret-token") in client.calls
    assert (
        "GET",
        "/study_phrase/check_exist/?word_id=101,102",
        "frontend-secret-token",
    ) in client.calls
    assert (
        "POST",
        "/transaction/send_tg_payment/",
        {"cost": 17},
    ) in client.request_bodies
    assert result.summary["study_id"] == 71
    assert result.summary["option_checks"] == [
        "book",
        "chapter",
        "language",
        "phrase",
        "study_phrase",
        "text_part",
        "transaction",
        "word",
    ]
    book_create_body = next(
        body
        for method, path, body in client.request_bodies
        if method == "POST" and path == "/book/" and body.get("name") == "Contract Book test-seed"
    )
    assert book_create_body["language_id"] == 1
    assert book_create_body["image"]["content"].startswith("data:image/png;base64,")
    book_patch_body = next(
        body
        for method, path, body in client.request_bodies
        if method == "PATCH" and path == "/book/22/"
    )
    assert book_patch_body["language_id"] == 1
    assert book_patch_body["description"] == "Contract smoke description patched"
    assert book_patch_body["image"]["name"] == "contract-cover-patched.png"
    assert book_patch_body["image"]["content"].startswith("data:image/png;base64,")
    first_chapter_body = next(
        body
        for method, path, body in client.request_bodies
        if method == "POST"
        and path == "/book/22/add_chapter/"
        and body.get("name") == "Contract First"
    )
    assert first_chapter_body["chapter_type"] == "articles"
    assert first_chapter_body["chapter_input"]["text"].startswith("alpha beta")
    assert "text" not in first_chapter_body
    second_chapter_body = next(
        body
        for method, path, body in client.request_bodies
        if method == "POST"
        and path == "/book/22/add_chapter/"
        and body.get("name") == "Contract Second"
    )
    assert second_chapter_body["chapter_type"] == "articles"
    assert second_chapter_body["chapter_input"]["text"].startswith("reader workers")
    assert "text" not in second_chapter_body
    assert client.generic_phrase_deleted is True
    assert client.generic_text_part_deleted is True
    assert client.second_chapter_deleted is True
    assert ("PATCH", "/account/profile/", "frontend-secret-token") in client.calls
    assert (
        "POST",
        "/account/send_link_to_tg/",
        "frontend-secret-token",
    ) in client.calls
    assert (
        "GET",
        "/study_phrase/check_exist/?word_id=101",
        "frontend-secret-token",
    ) in client.calls
    assert (
        "GET",
        "/study_phrase/check_exist/?text_part_id=51",
        "frontend-secret-token",
    ) in client.calls
    assert (
        "GET",
        "/study_phrase/check_exist/?phrase_id=61",
        "frontend-secret-token",
    ) in client.calls
    study_create_bodies = [
        body
        for method, path, body in client.request_bodies
        if method == "POST" and path == "/study_phrase/"
    ]
    assert {"is_active": True, "chapter_id": 31, "word_id": 101} in study_create_bodies
    assert {"is_active": True, "chapter_id": 31, "text_part_id": 51} in study_create_bodies
    assert {"is_active": True, "chapter_id": 31, "phrase_id": 61} in study_create_bodies
    assert (
        "PATCH",
        "/study_phrase/71/",
        {"is_active": False, "chapter_id": 31},
    ) in client.request_bodies
    assert "frontend-secret-token" not in str(result.to_dict())


def test_frontend_contract_smoke_fails_when_disabled_parser_contract_changes() -> None:
    from infrastructure.runtime.frontend_contract_smoke import (
        run_frontend_contract_smoke,
    )

    result = run_frontend_contract_smoke(
        client=FakeFrontendContractHttpClient(parser_disabled=False),
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        tg_user_id=994123456,
        seed="test-seed",
        chapter_ready_attempts=1,
        sleep=lambda _: None,
    )

    assert result.ok is False
    assert result.error_message is not None
    assert "parse_article disabled contract changed" in result.error_message
    assert result.steps[-1].name == "account_language_config"
    assert result.steps[-1].ok is False


def test_frontend_contract_smoke_fails_when_study_check_exist_mapping_is_wrong() -> None:
    from infrastructure.runtime.frontend_contract_smoke import (
        run_frontend_contract_smoke,
    )

    result = run_frontend_contract_smoke(
        client=FakeFrontendContractHttpClient(wrong_check_exist_mapping=True),
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        tg_user_id=994123456,
        seed="test-seed",
        chapter_ready_attempts=1,
        sleep=lambda _: None,
    )

    assert result.ok is False
    assert result.error_message is not None
    assert "study_phrase/check_exist phrase_id" in result.error_message
    assert result.steps[-1].name == "study_transaction_referral_contract"
    assert result.steps[-1].ok is False
