from __future__ import annotations
from application.abstract.services.crud import BaseCRUDService
from application.access_control.services import Accessor
from application.access_control.validators import OwnedByAccountValidator
from application.text.segment.dtos import SegmentDTO, SegmentListDTO, CreateSegmentDTO, UpdateSegmentDTO
from domain.text.segment.entities import SegmentEntity
from domain.text.segment.interfaces.repository import SegmentRepository
from domain.text.segment.exceptions import SegmentNotFoundError, SegmentPermissionDenied


class SegmentCrudService(
    BaseCRUDService[
        SegmentEntity,
        SegmentRepository,
        SegmentDTO,
        SegmentListDTO,
        CreateSegmentDTO,
        UpdateSegmentDTO
    ]
):
    """
    Service responsible for basic CRUD operations on SegmentEntity.
    """
    entity_class = SegmentEntity
    item_dto = SegmentDTO
    list_dto = SegmentListDTO
    not_found_exception = SegmentNotFoundError
    entity_repository_type = SegmentRepository
    entity_permission_denied_exception = SegmentPermissionDenied
