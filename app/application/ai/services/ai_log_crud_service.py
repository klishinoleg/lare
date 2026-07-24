from __future__ import annotations
from application.abstract.services.crud import BaseCRUDService
from application.ai.dtos.ai_log import AiLogDTO, UpdateAiLogDTO, AiLogListDTO, CreateAiLogDTO
from domain.ai.entities import AiLogEntity
from domain.ai.exceptions import AiLogNotFoundError, AiLogPermissionDenied
from domain.ai.interfaces.repository import AiLogRepository


class AiLogCRUDService(
    BaseCRUDService[
        AiLogEntity,
        AiLogRepository,
        AiLogDTO,
        AiLogListDTO,
        CreateAiLogDTO,
        UpdateAiLogDTO
    ]
):
    """
    Read-only service for querying AI interaction logs.
    """
    entity_class = AiLogEntity
    entity_repository_type = AiLogRepository
    item_dto = AiLogDTO
    list_dto = AiLogListDTO
    create_dto = CreateAiLogDTO
    update_dto = UpdateAiLogDTO
    not_found_exception = AiLogNotFoundError
    entity_permission_denied_exception = AiLogPermissionDenied

    def _set_acces_control_validators(self) -> None:
        ...
