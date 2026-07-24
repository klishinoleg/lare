from __future__ import annotations

from decimal import Decimal
from hashlib import sha256

from application.text.segment.services.segment_crud_service import SegmentCrudService
from core.di.repository import DIRepository
from core.enums.repository.types import RepositoryTypes
from domain.ai.entities import AiLogEntity, AiModelEntity
from domain.ai.interfaces.repository import AiLogRepository, AiModelRepository
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.text_data.enums import TextActionsTypes, TextTranslateTypes


class SegmentAiLogService:
    def __init__(self, repository_type: RepositoryTypes = RepositoryTypes.TORTOISE) -> None:
        self.repository_type = repository_type
        self.segment_service = SegmentCrudService(repository_type)
        self.ai_log_repo: AiLogRepository = DIRepository.get_repository(
            AiLogRepository,
            repository_type,
        )()
        self.ai_model_repo: AiModelRepository = DIRepository.get_repository(
            AiModelRepository,
            repository_type,
        )()

    async def ensure_request_log(
        self,
        *,
        account_id: int,
        segment_id: int,
        ai_model: str,
        action: TextActionsTypes,
        translate_type: TextTranslateTypes | None,
    ) -> AiLogEntity:
        segment = await self.segment_service.get_by_id(segment_id)
        usage_type = self._usage_type(action)
        ai_model_entity = await self._ensure_ai_model(ai_model, usage_type)
        hash_str = self._hash_request(
            account_id=account_id,
            segment_id=segment_id,
            source_language=segment.language_id,
            ai_model=ai_model,
            usage_type=usage_type,
            action=action,
            translate_type=translate_type,
            text=segment.name,
        )
        existing = await self.ai_log_repo.get_by_hash(
            hash_str=hash_str,
            usage_type=usage_type,
            ai_type="local",
        )
        if existing is not None:
            return existing

        saved = await self.ai_log_repo.save(
            AiLogEntity(
                ai_request=segment.name,
                ai_response="",
                ai_type="local",
                ai_model_id=ai_model_entity.id,
                file_path=None,
                source_language=segment.language_id,
                target_language=None
                if action == TextActionsTypes.VOICE
                else segment.language_id,
                usage_type=usage_type,
                account_id=account_id,
                hash_str=hash_str,
            )
        )
        if saved is None:
            raise RuntimeError("AI log was not saved.")
        return saved

    async def save_response(
        self,
        *,
        ai_log_id: int,
        content: str,
        action: TextActionsTypes,
    ) -> AiLogEntity | None:
        ai_log = await self.ai_log_repo.get_by_id(ai_log_id)
        if ai_log is None:
            return None
        if action == TextActionsTypes.VOICE:
            ai_log.file_path = content
        else:
            ai_log.ai_response = content
        return await self.ai_log_repo.save(ai_log)

    async def _ensure_ai_model(
        self,
        ai_model: str,
        usage_type: AccountUsageType,
    ) -> AiModelEntity:
        existing = await self.ai_model_repo.get_by_model(ai_model)
        if existing is not None:
            if usage_type not in existing.allow_to:
                existing.allow_to.append(usage_type)
                saved = await self.ai_model_repo.save(existing)
                if saved is None:
                    raise RuntimeError("AI model was not updated.")
                return saved
            return existing

        saved = await self.ai_model_repo.save(
            AiModelEntity(
                name=f"Local model: {ai_model}",
                model=ai_model,
                input_cost=Decimal("0"),
                output_cost=Decimal("0"),
                kef=1,
                allow_to=[usage_type],
            )
        )
        if saved is None:
            raise RuntimeError("AI model was not saved.")
        return saved

    @staticmethod
    def _usage_type(action: TextActionsTypes) -> AccountUsageType:
        if action == TextActionsTypes.VOICE:
            return AccountUsageType.AI_VOICE
        return AccountUsageType.AI_TRANSLATE

    @staticmethod
    def _hash_request(
        *,
        account_id: int,
        segment_id: int,
        source_language: int,
        ai_model: str,
        usage_type: AccountUsageType,
        action: TextActionsTypes,
        translate_type: TextTranslateTypes | None,
        text: str,
    ) -> str:
        payload = "|".join(
            [
                str(account_id),
                str(segment_id),
                str(source_language),
                ai_model,
                usage_type.value,
                action.value,
                translate_type.value if translate_type else "",
                " ".join(text.split()),
            ]
        )
        return sha256(payload.encode("utf-8")).hexdigest()
