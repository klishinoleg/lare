from dataclasses import dataclass, field
from abc import ABC


@dataclass
class WithActiveMixin(ABC):
    is_active: bool = field(repr=False, default_factory=lambda: True)

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False
