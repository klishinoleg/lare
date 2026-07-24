from domain.text_data.word.entities import WordVoiceEntity
from domain.text_data.word.interfaces.repository import WordVoiceRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import WordVoiceModel


class TortoiseWordVoiceRepository(
    BaseTortoiseRepository[WordVoiceEntity, WordVoiceModel],
    WordVoiceRepository,
):
    model = WordVoiceModel

    @staticmethod
    async def to_entity(o: WordVoiceModel) -> WordVoiceEntity:
        return WordVoiceEntity(
            id=o.id,
            word_id=o.word_id,
            file_path=o.file_path,
        )

    @BaseTortoiseRepository.read()
    async def get_by_word(self, word_id: int) -> WordVoiceEntity | None:
        obj = await self.model.filter(word_id=word_id).first()
        return await self.to_entity(obj) if obj else None
