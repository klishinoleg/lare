from pathlib import Path
import json
import aiofiles
import aiofiles.os
from .base import BaseDataStorage


class FileDataStorage[DT: list | dict](BaseDataStorage[DT, Path]):

    @staticmethod
    async def check_dir(path: Path) -> None:
        """
        Ensure that the parent directory of the path exists.

        Args:
            path (Path): The file path whose directory should exist.
        """
        if not aiofiles.os.path.exists(path):
            await aiofiles.os.makedirs(path.parent, exist_ok=True)

    async def save_json(self, path: Path, data: DT) -> None:
        """
        Save a dictionary to a JSON file asynchronously.

        Args:
            path (Path): Path to the JSON file.
            data (DT): Data to save.
        """
        await self.check_dir(path)
        async with aiofiles.open(path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))

    async def load_json(self, path: Path) -> DT:
        """
        Load a JSON file asynchronously.

        Args:
            path (Path): Path to the JSON file.

        Returns:
            dict: Loaded data.
        """
        async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)

    async def save_text(self, path: Path, text: str) -> None:
        """
        Save plain text to a file asynchronously.

        Args:
            path (Path): Path to the text file.
            text (str): Text to save.
        """
        await self.check_dir(path)
        async with aiofiles.open(path, mode='w', encoding='utf-8') as f:
            await f.write(text)

    async def load_text(self, path: Path) -> str:
        """
        Load plain text from a file asynchronously.

        Args:
            path (Path): Path to the text file.

        Returns:
            str: Loaded text.
        """
        async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
            return await f.read()
