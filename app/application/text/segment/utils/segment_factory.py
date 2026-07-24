from application.text.segment.dtos import CreateSegmentByWordChapterIndexesDTO
from application.text.segment.events import SegmentCreateRequestedEvent, SegmentErrorEvent
from core.di.events import DIPublisher
from domain.account.entities import AccountEntity
from domain.ai.entities import AiModelEntity


async def publish_segment_create_request_event(
    create_dto: CreateSegmentByWordChapterIndexesDTO,
    account: AccountEntity,
    ai_model_entity: AiModelEntity,
    pid: str | None = None,
) -> None:
    await DIPublisher[SegmentCreateRequestedEvent, SegmentErrorEvent].publish(
        payload=SegmentCreateRequestedEvent(
            account_id=account.id,
            dto=create_dto,
            ai_model=ai_model_entity.model,
            pid=pid,
        ),
        group_id=f"account:{account.id}",
    )


async def create_from_indexes_service(
    create_dto: CreateSegmentByWordChapterIndexesDTO,
    account: AccountEntity,
    ai_model_entity: AiModelEntity,
    pid: str | None = None,
) -> None:
    await publish_segment_create_request_event(create_dto, account, ai_model_entity, pid=pid)
