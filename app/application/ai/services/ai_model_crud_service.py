from __future__ import annotations

from application.abstract.services.crud import BaseCRUDService
from application.access_control.validators.administrator_validator import AdministratorValidator
from application.ai.dtos.ai_model import AiModelDTO, AiModelListDTO, CreateAiModelDTO, UpdateAiModelDTO
from domain.ai.entities import AiModelEntity
from domain.ai.interfaces.repository import AiModelRepository
from domain.ai.exceptions import AiModelNotFoundError, AiModelPermissionDenied
from application.access_control.services import Accessor


class AiModelCRUDService(
    BaseCRUDService[
        AiModelEntity,
        AiModelRepository,
        AiModelDTO,
        AiModelListDTO,
        CreateAiModelDTO,
        UpdateAiModelDTO
    ]
):
    """
    CRUD service for managing available AI models (admin only).
    """
    entity_class = AiModelEntity
    entity_repository_type = AiModelRepository
    item_dto = AiModelDTO
    list_dto = AiModelListDTO
    not_found_exception = AiModelNotFoundError
    entity_permission_denied_exception = AiModelPermissionDenied

    def _set_acces_control_validators(self) -> None:
        Accessor.register(self.entity_class, AdministratorValidator(), self.entity_permission_denied_exception)
