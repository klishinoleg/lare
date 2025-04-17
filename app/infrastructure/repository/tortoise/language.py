from domain.language.entities import LanguageEntity
from domain.language.interfaces.repository import LanguageRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models.language import LanguageModel


class TortoiseLanguageRepository(BaseTortoiseRepository[LanguageEntity, LanguageModel], LanguageRepository):
    model = LanguageModel

    @staticmethod
    async def to_entity(o: LanguageModel) -> LanguageEntity:
        return LanguageEntity(
            id=o.id,
            name=o.name,
            slug=o.slug,
            code=o.code,
            original_name=o.original_name,
            ordering=o.ordering
        )
