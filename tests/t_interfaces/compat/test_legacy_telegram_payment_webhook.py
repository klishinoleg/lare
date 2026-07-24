from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from application.events.handlers_register.finance import register_finance_main_brokers
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from core.enums.payment.payment_service import PaymentService
from domain.access_role.enums.roles import AccessRole
from domain.finance.enums.currency import Currency
from domain.finance.enums.transaction_type import TransactionType
from infrastructure.broker.mock.broker import MockEventBroker
from infrastructure.broker.mock.publisher import MockPublisher
from infrastructure.repository.tortoise.models import (
    AccessRoleModel,
    AccountModel,
    AccountTransactionModel,
    BillModel,
)


@pytest.mark.asyncio
async def test_legacy_telegram_webhook_successful_payment_confirms_bill(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-telegram-payment-webhook.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    MockPublisher.clear_events()
    MockEventBroker.subscribers.clear()

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        register_finance_main_brokers(EventBrokerTypes.MOCK, bills=True)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106001,
                            "username": "payment_webhook",
                            "first_name": "Payment",
                            "last_name": "Webhook",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            auth_data = auth_response.json()
            account_id = auth_data["account"]["id"]
            headers = {"Authorization": f"Token {auth_data['token']}"}

            bill_response = await client.post(
                "/api/v1/transaction/send_tg_payment/",
                headers=headers,
                json={"cost": 21},
            )
            assert bill_response.status_code == 200
            bill_id = bill_response.json()["bill_id"]

            webhook_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106001,
                    "message": {
                        "message_id": 7101,
                        "date": 1,
                        "chat": {"id": 9106001, "type": "private"},
                        "successful_payment": {
                            "currency": "XTR",
                            "total_amount": 21,
                            "invoice_payload": str(bill_id),
                            "telegram_payment_charge_id": "tg-webhook-charge-ok",
                            "provider_payment_charge_id": "provider-webhook-charge-ok",
                        },
                    },
                },
            )
            transactions_response = await client.get(
                "/api/v1/transaction/?transaction_type=payment",
                headers=headers,
            )

        assert webhook_response.status_code == 200
        assert webhook_response.json() == {
            "success": True,
            "handled": "successful_payment",
            "bill_id": bill_id,
        }
        assert transactions_response.status_code == 200
        assert any(
            item["bill_id"] == bill_id
            for item in transactions_response.json()["results"]
        )

        account = await AccountModel.get(id=account_id)
        bill = await BillModel.get(id=bill_id)
        transaction = await AccountTransactionModel.get(
            account_id=account_id,
            bill_id=bill_id,
            transaction_type=TransactionType.PAYMENT,
        )

        assert bill.success_time is not None
        assert bill.transaction == "tg-webhook-charge-ok"
        assert transaction.credits_amount == Decimal("21.00")
        assert account.credits == Decimal("21.00")
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_telegram_webhook_manual_bill_admin_flow_confirms_credits(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-telegram-manual-bill-webhook.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    MockPublisher.clear_events()
    MockEventBroker.subscribers.clear()

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        register_finance_main_brokers(EventBrokerTypes.MOCK, bills=True)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin_auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106101,
                            "username": "manual_admin",
                            "first_name": "Manual",
                            "last_name": "Admin",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert admin_auth_response.status_code == 200
            admin_account_id = admin_auth_response.json()["account"]["id"]
            await AccessRoleModel.create(
                account_id=admin_account_id,
                role=AccessRole.SUPERUSER,
            )

            target_auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106102,
                            "username": "manual_target",
                            "first_name": "Manual",
                            "last_name": "Target",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert target_auth_response.status_code == 200
            target_account_id = target_auth_response.json()["account"]["id"]

            create_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106101,
                    "message": {
                        "message_id": 8101,
                        "date": 1,
                        "chat": {"id": 9106101, "type": "private"},
                        "from": {"id": 9106101, "is_bot": False, "first_name": "Manual"},
                        "text": f"credits:{target_account_id}:15:150:RUB",
                    },
                },
            )

            assert create_response.status_code == 200
            create_payload = create_response.json()
            bill_id = create_payload["bill_id"]

            confirm_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106102,
                    "callback_query": {
                        "id": "manual-confirm-1",
                        "from": {"id": 9106101, "is_bot": False, "first_name": "Manual"},
                        "message": {
                            "message_id": 8102,
                            "date": 1,
                            "chat": {"id": 9106101, "type": "private"},
                        },
                        "data": f"manual_bill_{bill_id}_yes",
                    },
                },
            )

        assert create_payload["success"] is True
        assert create_payload["handled"] == "manual_bill_created"
        assert create_payload["target_account_id"] == target_account_id
        assert create_payload["credits_amount"] == 15.0
        assert create_payload["cost"] == 150
        assert create_payload["currency"] == Currency.RUB.value
        assert create_payload["keyboard"] == [
            [
                {"text": "YES", "callback_data": f"manual_bill_{bill_id}_yes"},
                {"text": "NO", "callback_data": f"manual_bill_{bill_id}_no"},
            ]
        ]

        assert confirm_response.status_code == 200
        assert confirm_response.json() == {
            "success": True,
            "handled": "manual_bill_confirmed",
            "bill_id": bill_id,
            "target_account_id": target_account_id,
            "text": f"Manual bill {bill_id} confirmed for account {target_account_id}.",
        }

        target = await AccountModel.get(id=target_account_id)
        bill = await BillModel.get(id=bill_id)
        transaction = await AccountTransactionModel.get(
            account_id=target_account_id,
            bill_id=bill_id,
            transaction_type=TransactionType.PAYMENT,
        )

        assert bill.payment_service == PaymentService.MANUAL
        assert bill.currency == Currency.RUB
        assert bill.success_time is not None
        assert bill.transaction == f"telegram:9106101:{bill_id}"
        assert transaction.credits_amount == Decimal("15.00")
        assert target.credits == Decimal("15.00")
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_telegram_webhook_admin_bonus_grants_manual_credits(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-telegram-admin-bonus-webhook.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    MockPublisher.clear_events()
    MockEventBroker.subscribers.clear()

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        register_finance_main_brokers(EventBrokerTypes.MOCK, bills=True)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin_auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106201,
                            "username": "bonus_admin",
                            "first_name": "Bonus",
                            "last_name": "Admin",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert admin_auth_response.status_code == 200
            admin_account_id = admin_auth_response.json()["account"]["id"]
            await AccessRoleModel.create(
                account_id=admin_account_id,
                role=AccessRole.SUPERUSER,
            )

            target_auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106202,
                            "username": "bonus_target",
                            "first_name": "Bonus",
                            "last_name": "Target",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert target_auth_response.status_code == 200
            target_account_id = target_auth_response.json()["account"]["id"]

            response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106201,
                    "message": {
                        "message_id": 8201,
                        "date": 1,
                        "chat": {"id": 9106201, "type": "private"},
                        "from": {"id": 9106201, "is_bot": False, "first_name": "Bonus"},
                        "text": f"/bonus {target_account_id} 25.50",
                    },
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["handled"] == "admin_bonus_granted"
        assert payload["target_account_id"] == target_account_id
        assert payload["credits_amount"] == 25.5

        target = await AccountModel.get(id=target_account_id)
        transaction = await AccountTransactionModel.get(
            account_id=target_account_id,
            transaction_type=TransactionType.MANUAL,
        )

        assert transaction.bill_id is None
        assert transaction.credits_amount == Decimal("25.50")
        assert target.credits == Decimal("25.50")
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_telegram_webhook_config_admin_credit_alias_grants_manual_credits(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-telegram-config-admin-credit-webhook.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.telegram_admin_user_ids = "9106301"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    MockPublisher.clear_events()
    MockEventBroker.subscribers.clear()

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        register_finance_main_brokers(EventBrokerTypes.MOCK, bills=True)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin_auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106301,
                            "username": "config_bonus_admin",
                            "first_name": "Config",
                            "last_name": "Admin",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert admin_auth_response.status_code == 200

            target_auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106302,
                            "username": "config_bonus_target",
                            "first_name": "Config",
                            "last_name": "Target",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert target_auth_response.status_code == 200
            target_account_id = target_auth_response.json()["account"]["id"]

            response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106301,
                    "message": {
                        "message_id": 8301,
                        "date": 1,
                        "chat": {"id": 9106301, "type": "private"},
                        "from": {"id": 9106301, "is_bot": False, "first_name": "Config"},
                        "text": f"/credit {target_account_id} 7.25",
                    },
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["handled"] == "admin_bonus_granted"
        assert payload["credits_amount"] == 7.25

        target = await AccountModel.get(id=target_account_id)
        transaction = await AccountTransactionModel.get(
            account_id=target_account_id,
            transaction_type=TransactionType.MANUAL,
        )

        assert transaction.credits_amount == Decimal("7.25")
        assert target.credits == Decimal("7.25")
    finally:
        settings.telegram_admin_user_ids = ""
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_telegram_webhook_admin_credit_command_without_args_returns_help(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-telegram-admin-credit-help-webhook.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.telegram_admin_user_ids = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    MockPublisher.clear_events()
    MockEventBroker.subscribers.clear()

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106302,
                    "message": {
                        "message_id": 8302,
                        "date": 1,
                        "chat": {"id": 9106303, "type": "private"},
                        "from": {"id": 9106303, "is_bot": False, "first_name": "Help"},
                        "text": "/add",
                    },
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["handled"] == "help"
        assert "/bonus <account_id> <credits>" in payload["text"]
        assert "credits:<account_id>:<credits>:<cost>:RUB" in payload["text"]
    finally:
        await close_tortoise()
