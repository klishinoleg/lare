from __future__ import annotations

from typing import Any

from infrastructure.runtime.legacy_compat_smoke import HttpResponse


class FakeReaderActionsHttpClient:
    def __init__(self, *, dialog_has_assistant: bool = True) -> None:
        self.dialog_has_assistant = dialog_has_assistant
        self.calls: list[tuple[str, str, str | None]] = []
        self.request_bodies: list[tuple[str, str, dict[str, Any] | None]] = []

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
        self.request_bodies.append((method, path, body))
        if method == "POST" and path == "/account/telegram_auth/":
            return HttpResponse(
                status=200,
                data={"token": "reader-secret-token", "account": {"id": 10}},
            )
        if method == "GET" and path == "/language/":
            return HttpResponse(status=200, data=[{"id": 1, "code": "en"}])
        if method == "POST" and path == "/book/generate/":
            return HttpResponse(
                status=200,
                data={
                    "count": 1,
                    "results": [{"id": 20, "name": "Generated", "chapters": [{"id": 30}]}],
                },
            )
        if method == "POST" and path == "/book/generate_chapters/":
            return HttpResponse(
                status=200,
                data={
                    "id": 20,
                    "chapters": [{"id": 30}, {"id": 31}],
                    "chapters_count": 2,
                },
            )
        if method == "GET" and path in {"/chapter/30/", "/chapter/31/"}:
            chapter_id = 30 if path == "/chapter/30/" else 31
            return HttpResponse(status=200, data=self._chapter(chapter_id))
        if method == "POST" and path == "/book/generate_image/":
            return HttpResponse(status=200, data={"source": "data:image/png;base64,abc"})
        if method == "POST" and path == "/text_part/create_from_indexes/":
            if body and body.get("action") == "create_voice":
                return HttpResponse(
                    status=200,
                    data={
                        "id": 41,
                        "name": "alpha beta gamma",
                        "words": [{"id": 1}],
                        "ai_voice": {
                            "file": "/uploads/compat_voice/text_part.wav",
                        },
                    },
                )
            return HttpResponse(
                status=200,
                data={
                    "id": 40,
                    "name": "alpha beta gamma",
                    "words": [{"id": 1}],
                    "translate": {"translate": "translated text"},
                },
            )
        if method == "GET" and path == "/text_part/40/dialog/":
            return HttpResponse(status=200, data={"id": 50, "text_part": 40, "dialog": []})
        if method == "POST" and path == "/text_part/40/dialog/":
            dialog = [{"role": "user", "content": "Explain it."}]
            if self.dialog_has_assistant:
                dialog.append({"role": "assistant", "content": "Explanation."})
            return HttpResponse(status=200, data={"id": 50, "text_part": 40, "dialog": dialog})
        if method == "POST" and path == "/phrase/create_from_indexes/":
            return HttpResponse(
                status=200,
                data=[{"id": 60, "name": "beta gamma", "words": [{"id": 2}]}],
            )
        if method == "GET" and path == "/phrase/60/create_voice/":
            return HttpResponse(
                status=200,
                data={"id": 60, "ai_voice": {"file": "/uploads/compat_voice/phrase.wav"}},
            )
        if method == "GET" and path == "/word/100/":
            return HttpResponse(
                status=200,
                data=self._word_translate(ai_word=False),
            )
        if method == "GET" and path == "/word/70/create_etymology/":
            return HttpResponse(
                status=200,
                data=self._word_translate(ai_word=True),
            )
        if method == "GET" and path == "/word/70/get_etymology/":
            return HttpResponse(
                status=200,
                data=self._word_translate(ai_word=True),
            )
        if method == "POST" and path == "/study_phrase/create_word_voice/":
            return HttpResponse(
                status=200,
                data={"id": 100, "ai_voice": {"file": "/uploads/compat_voice/word.wav"}},
            )
        if method == "POST" and path == "/study_phrase/":
            return HttpResponse(
                status=200,
                data={"id": 80, "word": {"id": 100}, "text_part": {"id": 40}, "phrase": {"id": 60}},
            )
        if method == "GET" and path == "/study_phrase/80/create_voice/":
            return HttpResponse(status=200, data={"id": 80, "word": {"id": 100}})
        if method == "GET" and path == "/study_phrase/":
            return HttpResponse(status=200, data={"count": 1, "results": [{"id": 80}]})
        if method == "GET" and path == "/transaction/?transaction_type=ai_usage":
            return HttpResponse(status=200, data={"count": 6, "results": []})
        raise AssertionError(f"Unexpected request: {method} {path}")

    def _chapter(self, chapter_id: int) -> dict[str, Any]:
        return {
            "id": chapter_id,
            "is_ready": True,
            "content": [
                {"id": 1, "name": "alpha", "w": 100},
                {"id": 2, "name": "beta", "w": 101},
                {"id": 3, "name": "gamma", "w": 102},
                {"id": 4, "name": "delta", "w": 103},
                {"id": 5, "name": "epsilon", "w": 104},
                {"id": 6, "name": "zeta", "w": 105},
                {"id": 7, "name": "eta", "w": 106},
                {"id": 8, "name": "theta", "w": 107},
                {"id": 9, "name": "iota", "w": 108},
                {"id": 10, "name": "kappa", "w": 109},
                {"id": 11, "name": "lambda", "w": 110},
                {"id": 12, "name": "mu", "w": 111},
            ],
        }

    def _word_translate(self, *, ai_word: bool) -> dict[str, Any]:
        etymology = {"description": "root explanation"} if ai_word else None
        root = (
            {
                "id": 900,
                "name": "alph",
                "translate": {"description": "root explanation"},
            }
            if ai_word
            else None
        )
        return {
            "id": 70,
            "type": "WRD",
            "translate": "alpha",
            "transliteration": "alpha",
            "gender": None,
            "ai_word": ai_word,
            "word": {
                "id": 100,
                "name": "alpha",
                "ai_voice": None,
                "etymology": etymology,
                "root": root,
                "word_parts": [
                    {
                        "id": 901,
                        "name": "alph",
                        "translate": {"description": "root explanation"},
                    },
                ],
                "related_words": [],
            },
        }


def fake_upload_fetcher(path: str) -> dict[str, Any]:
    return {"path": path, "status": 200, "content_type": "audio/wav", "byte_length": 256}


def test_reader_actions_smoke_runs_paid_reader_intelligence_contract() -> None:
    from infrastructure.runtime.reader_actions_smoke import run_reader_actions_smoke

    client = FakeReaderActionsHttpClient()

    result = run_reader_actions_smoke(
        client=client,
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        tg_user_id=992123456,
        seed="test-seed",
        chapter_ready_attempts=1,
        sleep=lambda _: None,
        check_upload_files=True,
        upload_fetcher=fake_upload_fetcher,
    )

    assert result.ok is True
    assert result.summary["account_id"] == 10
    assert result.summary["book_id"] == 20
    assert result.summary["generated_chapter_id"] == 31
    assert result.summary["generated_book_payload_language_level"] == "a1"
    assert result.summary["generated_book_payload_chapter_type"] == "story"
    assert result.summary["generated_chapters_payload_language_level"] == "a1"
    assert result.summary["generated_chapters_payload_chapter_type"] == "story"
    assert result.summary["text_part_id"] == 40
    assert result.summary["phrase_id"] == 60
    assert result.summary["word_translate_id"] == 70
    assert result.summary["word_render_type"] == "WRD"
    assert result.summary["word_render_name"] == "alpha"
    assert result.summary["word_render_translate"] == "alpha"
    assert result.summary["word_render_transliteration"] == "alpha"
    assert result.summary["word_etymology_root_name"] == "alph"
    assert result.summary["word_etymology_root_description"] == "root explanation"
    assert result.summary["word_etymology_part_count"] == 1
    assert result.summary["study_id"] == 80
    assert result.summary["ai_usage_transaction_count"] == 6
    assert result.summary["text_part_voice_file"] == "/uploads/compat_voice/text_part.wav"
    assert result.summary["upload_checks"]["phrase"]["byte_length"] == 256
    assert result.summary["upload_checks"]["text_part"]["byte_length"] == 256
    assert ("POST", "/text_part/40/dialog/", "reader-secret-token") in client.calls
    assert (
        "POST",
        "/book/generate/",
        {
            "language_id": 1,
            "language_level": "a1",
            "chapter_type": "story",
            "description": (
                "Reader actions smoke test-seed. "
                "Generate enough words for dialog voice and etymology."
            ),
        },
    ) in client.request_bodies
    assert (
        "POST",
        "/book/generate_chapters/",
        {
            "book_id": 20,
            "language_id": 1,
            "language_level": "a1",
            "chapter_type": "story",
            "description": "Generated reader action chapter test-seed.",
        },
    ) in client.request_bodies
    assert (
        "POST",
        "/text_part/create_from_indexes/",
        {"indexes": [1, 2, 3, 4, 5, 6], "action": "create_voice"},
    ) in client.request_bodies
    assert "reader-secret-token" not in str(result.to_dict())


def test_reader_actions_smoke_fails_when_dialog_has_no_assistant_reply() -> None:
    from infrastructure.runtime.reader_actions_smoke import run_reader_actions_smoke

    result = run_reader_actions_smoke(
        client=FakeReaderActionsHttpClient(dialog_has_assistant=False),
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        tg_user_id=992123456,
        seed="test-seed",
        chapter_ready_attempts=1,
        sleep=lambda _: None,
    )

    assert result.ok is False
    assert result.error_message is not None
    assert "Dialog send contract failed" in result.error_message
    assert result.steps[-1].name == "text_dialog_contract"
    assert result.steps[-1].ok is False
