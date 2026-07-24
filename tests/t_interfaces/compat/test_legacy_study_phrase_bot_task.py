from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from infrastructure.repository.tortoise.models import CompatStudyPhraseLogModel


@pytest.mark.asyncio
async def test_legacy_telegram_action_callback_creates_and_rates_study_task(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-study-phrase-bot-task.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    settings.web_app_url = "https://lang-reader.test/"

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9108001,
                            "username": "study_task",
                            "first_name": "Study",
                            "last_name": "Task",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            headers = {"Authorization": f"Token {auth_response.json()['token']}"}

            book_response = await client.post(
                "/api/v1/book/",
                headers=headers,
                json={"name": "Study task book", "language": 1},
            )
            assert book_response.status_code == 200
            book_id = book_response.json()["id"]

            add_chapter_response = await client.post(
                f"/api/v1/book/{book_id}/add_chapter/",
                headers=headers,
                json={
                    "name": "Study task chapter",
                    "chapter_input": {"text": "hello task world"},
                },
            )
            assert add_chapter_response.status_code == 200
            chapter_id = add_chapter_response.json()["chapters"][0]["id"]

            chapter_response = await client.get(
                f"/api/v1/chapter/{chapter_id}/",
                headers=headers,
            )
            assert chapter_response.status_code == 200
            task_token = next(
                item for item in chapter_response.json()["content"] if item["name"] == "task"
            )

            create_study_response = await client.post(
                "/api/v1/study_phrase/",
                headers=headers,
                json={
                    "chapter_id": chapter_id,
                    "word_id": task_token["w"],
                    "is_active": True,
                },
            )
            assert create_study_response.status_code == 200
            study_id = create_study_response.json()["id"]

            task_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99108001,
                    "callback_query": {
                        "id": "callback-study-task-1",
                        "from": {
                            "id": 9108001,
                            "is_bot": False,
                            "first_name": "Study",
                            "username": "study_task",
                            "language_code": "en",
                        },
                        "message": {
                            "message_id": 8108,
                            "date": 1,
                            "chat": {"id": 9108001, "type": "private"},
                        },
                        "data": "action_1",
                    },
                },
            )
            assert task_response.status_code == 200
            task_payload = task_response.json()
            log_id = task_payload["log_id"]

            rating_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99108002,
                    "callback_query": {
                        "id": "callback-study-task-rating-1",
                        "from": {
                            "id": 9108001,
                            "is_bot": False,
                            "first_name": "Study",
                            "username": "study_task",
                            "language_code": "en",
                        },
                        "message": {
                            "message_id": 8108,
                            "date": 1,
                            "chat": {"id": 9108001, "type": "private"},
                        },
                        "data": f"study_phrase_{log_id}_3",
                    },
                },
            )

            study_response = await client.get(
                f"/api/v1/study_phrase/{study_id}/",
                headers=headers,
            )

        assert task_payload["success"] is True
        assert task_payload["handled"] == "study_task_created"
        assert task_payload["study_phrase_id"] == study_id
        assert task_payload["study_type"] == "forward"
        assert task_payload["text"].startswith("task")
        assert task_payload["web_app_url"] == "https://lang-reader.test?study=1"
        assert task_payload["keyboard"][0] == [
            {"text": "1", "callback_data": f"study_phrase_{log_id}_1"},
            {"text": "2", "callback_data": f"study_phrase_{log_id}_2"},
            {"text": "3", "callback_data": f"study_phrase_{log_id}_3"},
            {"text": "4", "callback_data": f"study_phrase_{log_id}_4"},
            {"text": "5", "callback_data": f"study_phrase_{log_id}_5"},
        ]

        log = await CompatStudyPhraseLogModel.get(id=log_id)
        assert log.study_phrase_id == study_id
        assert log.study_type == "forward"
        assert log.is_active is True

        assert rating_response.status_code == 200
        study = study_response.json()
        assert study["success_logs"] == 1
        assert study["forward_average"] == 3
        assert study["average"] == 3
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_telegram_reset_tasks_removes_pending_study_logs(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-study-phrase-bot-reset.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9108003,
                            "username": "study_reset",
                            "first_name": "Study",
                            "last_name": "Reset",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            headers = {"Authorization": f"Token {auth_response.json()['token']}"}

            book_response = await client.post(
                "/api/v1/book/",
                headers=headers,
                json={"name": "Study reset book", "language": 1},
            )
            assert book_response.status_code == 200
            book_id = book_response.json()["id"]

            add_chapter_response = await client.post(
                f"/api/v1/book/{book_id}/add_chapter/",
                headers=headers,
                json={
                    "name": "Study reset chapter",
                    "chapter_input": {"text": "hello reset task world"},
                },
            )
            assert add_chapter_response.status_code == 200
            chapter_id = add_chapter_response.json()["chapters"][0]["id"]

            chapter_response = await client.get(
                f"/api/v1/chapter/{chapter_id}/",
                headers=headers,
            )
            assert chapter_response.status_code == 200
            reset_token = next(
                item for item in chapter_response.json()["content"] if item["name"] == "reset"
            )

            create_study_response = await client.post(
                "/api/v1/study_phrase/",
                headers=headers,
                json={
                    "chapter_id": chapter_id,
                    "word_id": reset_token["w"],
                    "is_active": True,
                },
            )
            assert create_study_response.status_code == 200

            task_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99108004,
                    "callback_query": {
                        "id": "callback-study-reset-task-1",
                        "from": {
                            "id": 9108003,
                            "is_bot": False,
                            "first_name": "Study",
                            "username": "study_reset",
                            "language_code": "en",
                        },
                        "message": {
                            "message_id": 8110,
                            "date": 1,
                            "chat": {"id": 9108003, "type": "private"},
                        },
                        "data": "action_1",
                    },
                },
            )
            assert task_response.status_code == 200
            log_id = task_response.json()["log_id"]

            reset_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99108005,
                    "message": {
                        "message_id": 8111,
                        "date": 1,
                        "chat": {"id": 9108003, "type": "private"},
                        "from": {
                            "id": 9108003,
                            "is_bot": False,
                            "first_name": "Study",
                            "username": "study_reset",
                            "language_code": "en",
                        },
                        "text": "/reset_tasks",
                    },
                },
            )

        assert reset_response.status_code == 200
        assert reset_response.json() == {
            "success": True,
            "handled": "study_tasks_reset",
            "count": 1,
        }
        assert await CompatStudyPhraseLogModel.get_or_none(id=log_id) is None
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_telegram_action_delete_callback_is_accepted(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-study-phrase-bot-action-delete.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9108002,
                            "username": "study_delete",
                            "first_name": "Study",
                            "last_name": "Delete",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200

            delete_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99108003,
                    "callback_query": {
                        "id": "callback-study-task-delete-1",
                        "from": {
                            "id": 9108002,
                            "is_bot": False,
                            "first_name": "Study",
                            "username": "study_delete",
                            "language_code": "en",
                        },
                        "message": {
                            "message_id": 8109,
                            "date": 1,
                            "chat": {"id": 9108002, "type": "private"},
                        },
                        "data": "action_4",
                    },
                },
            )

        assert delete_response.status_code == 200
        assert delete_response.json() == {
            "success": True,
            "handled": "study_task_deleted",
            "chat_id": 9108002,
            "message_id": 8109,
        }
    finally:
        await close_tortoise()
