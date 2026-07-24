from domain.text_data.word.entities import WordTranslateEntity
from domain.text_data.word.interfaces.repository import WordTranslateRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import WordTranslateModel


class TortoiseWordTranslateRepository(
    BaseTortoiseRepository[WordTranslateEntity, WordTranslateModel],
    WordTranslateRepository,
):
    model = WordTranslateModel

    @staticmethod
    async def to_entity(o: WordTranslateModel) -> WordTranslateEntity:
        return WordTranslateEntity(
            id=o.id,
            word_id=o.word_id,
            language_id=o.language_id,
            account_id=o.account_id,
            translate=o.translate,
            transliteration=o.transliteration,
            word_type=o.word_type,
            gender=o.gender,
        )

    @BaseTortoiseRepository.read()
    async def get_by_word(self, word_id: int, language_id: int, account_id: int) -> WordTranslateEntity | None:
        obj = await self.model.filter(
            word_id=word_id,
            language_id=language_id,
            account_id=account_id
        ).first()
        return await self.to_entity(obj) if obj else None
