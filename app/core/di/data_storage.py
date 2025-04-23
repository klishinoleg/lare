from core.enums.storage.data import DataStorageTypes
from infrastructure.data_storage.base import BaseDataStorage
from infrastructure.data_storage.file import FileDataStorage


class DIDataStorage[DT: list | dict, DS: BaseDataStorage]:
    @staticmethod
    def get(storage_type: DataStorageTypes = DataStorageTypes.FILE) -> DS:
        if storage_type == DataStorageTypes.FILE:
            return FileDataStorage()
        else:
            raise AttributeError("Storage {} not found".format(storage_type))
