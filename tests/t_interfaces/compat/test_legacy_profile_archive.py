from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes


BOOK_IMAGE_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+"
    "M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@pytest.mark.asyncio
async def test_legacy_profile_and_archive_routes_match_old_backend(tmp_path) -> None:
    db_path = tmp_path / "legacy-profile-archive.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
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
                            "id": 9101001,
                            "username": "profile_archive",
                            "first_name": "Profile",
                            "last_name": "Archive",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            auth_data = auth_response.json()
            headers = {"Authorization": f"Token {auth_data['token']}"}

            book_response = await client.post(
                "/api/v1/book/",
                headers=headers,
                json={"name": "Archived compatible book", "language": 1},
            )
            assert book_response.status_code == 200

            profile_response = await client.get("/api/v1/account/profile/", headers=headers)
            archive_response = await client.get("/api/v1/book/archive/", headers=headers)

        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["id"] == auth_data["account"]["id"]
        assert profile["username"].startswith("TG:9101001")
        assert profile["language_id"] == auth_data["account"]["language_id"]

        assert archive_response.status_code == 200
        archive = archive_response.json()
        assert isinstance(archive, list)
        assert [item["id"] for item in archive] == [book_response.json()["id"]]
        assert archive[0]["name"] == "Archived compatible book"
        assert "chapters" in archive[0]
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_book_archive_state_hides_inactive_books_from_main_list(tmp_path) -> None:
    db_path = tmp_path / "legacy-book-archive-state.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
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
                            "id": 9101002,
                            "username": "book_archive_state",
                            "first_name": "Book",
                            "last_name": "Archive",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            headers = {"Authorization": f"Token {auth_response.json()['token']}"}

            active_response = await client.post(
                "/api/v1/book/",
                headers=headers,
                json={"name": "Still active book", "language": 1},
            )
            archived_response = await client.post(
                "/api/v1/book/",
                headers=headers,
                json={"name": "Archived by UI toggle", "language": 1},
            )
            assert active_response.status_code == 200
            assert archived_response.status_code == 200
            archived_book_id = archived_response.json()["id"]

            patch_response = await client.patch(
                f"/api/v1/book/{archived_book_id}/",
                headers=headers,
                json={"is_active": False},
            )
            list_response = await client.get("/api/v1/book/", headers=headers)
            archive_response = await client.get("/api/v1/book/archive/", headers=headers)

        assert patch_response.status_code == 200
        assert patch_response.json()["is_active"] is False

        assert list_response.status_code == 200
        listed_books = list_response.json()["results"]
        assert [book["id"] for book in listed_books] == [active_response.json()["id"]]
        assert all(book["is_active"] is True for book in listed_books)

        assert archive_response.status_code == 200
        archive_by_id = {book["id"]: book for book in archive_response.json()}
        assert archive_by_id[active_response.json()["id"]]["is_active"] is True
        assert archive_by_id[archived_book_id]["is_active"] is False
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_book_update_persists_description_for_edit_modal(tmp_path) -> None:
    db_path = tmp_path / "legacy-book-update-description.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
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
                            "id": 9101003,
                            "username": "book_update_description",
                            "first_name": "Book",
                            "last_name": "Description",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            headers = {"Authorization": f"Token {auth_response.json()['token']}"}

            create_response = await client.post(
                "/api/v1/book/",
                headers=headers,
                json={
                    "name": "Editable compatible book",
                    "language": 1,
                    "description": "Initial modal description",
                },
            )
            assert create_response.status_code == 200
            book_id = create_response.json()["id"]

            patch_response = await client.patch(
                f"/api/v1/book/{book_id}/",
                headers=headers,
                json={
                    "name": "Edited compatible book",
                    "language": 1,
                    "description": "Updated modal description",
                },
            )
            get_response = await client.get(f"/api/v1/book/{book_id}/", headers=headers)

        assert patch_response.status_code == 200
        patched_book = patch_response.json()
        assert patched_book["name"] == "Edited compatible book"
        assert patched_book["description"] == "Updated modal description"

        assert get_response.status_code == 200
        loaded_book = get_response.json()
        assert loaded_book["description"] == "Updated modal description"
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_book_update_accepts_edit_modal_image_payload(tmp_path) -> None:
    db_path = tmp_path / "legacy-book-update-image.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
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
                            "id": 9101004,
                            "username": "book_update_image",
                            "first_name": "Book",
                            "last_name": "Image",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            headers = {"Authorization": f"Token {auth_response.json()['token']}"}

            create_response = await client.post(
                "/api/v1/book/",
                headers=headers,
                json={
                    "name": "Image compatible book",
                    "language_id": 1,
                    "description": "Initial image modal description",
                    "image": {
                        "name": "initial-cover.png",
                        "type": "image/png",
                        "size": 68,
                        "content": BOOK_IMAGE_DATA_URL,
                    },
                },
            )
            assert create_response.status_code == 200
            book_id = create_response.json()["id"]

            patch_response = await client.patch(
                f"/api/v1/book/{book_id}/",
                headers=headers,
                json={
                    "name": "Image compatible book edited",
                    "language_id": 1,
                    "description": "Updated image modal description",
                    "image": {
                        "name": "edited-cover.png",
                        "type": "image/png",
                        "size": 68,
                        "content": BOOK_IMAGE_DATA_URL,
                    },
                },
            )
            get_response = await client.get(f"/api/v1/book/{book_id}/", headers=headers)

        assert patch_response.status_code == 200
        patched_book = patch_response.json()
        assert patched_book["description"] == "Updated image modal description"
        assert patched_book["image"].startswith("/uploads/compat_books/")
        assert patched_book["croped_image"].startswith("/uploads/compat_books/")

        assert get_response.status_code == 200
        loaded_book = get_response.json()
        assert loaded_book["image"] == patched_book["image"]
    finally:
        await close_tortoise()
