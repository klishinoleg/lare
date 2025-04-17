from dataclasses import dataclass, field
from datetime import datetime, timezone
from abc import ABC


@dataclass
class TimestampMixin(ABC):
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc), repr=False)
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc), repr=False)

    def set_update_now(self):
        self.updated_at = datetime.now(tz=timezone.utc)
        return self
