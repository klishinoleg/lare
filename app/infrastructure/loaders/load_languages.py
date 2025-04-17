from __future__ import annotations

import csv
from pathlib import Path
from domain.language.entities import LanguageEntity


def load_languages_init_entities(limit: int | None = None) -> list[LanguageEntity]:
    """
    Load languages from a CSV file and return as list of LanguageEntity.
    CSV must have headers: name,slug,code,original_name,ordering

    Args:

    Returns:
        list[LanguageEntity]: Parsed entities.
    """
    file_path = Path(__file__).parent.parent.parent / "static" / "initial_data" / "languages.csv"
    entities: list[LanguageEntity] = []

    with file_path.open(encoding="utf-8") as f:
        reader: list[dict[str, str | int | None]] = csv.DictReader(f)
        n = 0
        for row in reader:
            n += 1
            if limit and n > limit:
                break
            entities.append(LanguageEntity(
                id=int(row["id"]),
                name=row["name"],
                ordering=int(row.get("ordering") or "100"),
                original_name=row["original_name"],
                code=row["code"],
                slug=row["slug"],
            ))
    return entities
