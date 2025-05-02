from __future__ import annotations
from domain.abstract import BaseEntity
from core.i18n import _


class GetActMessages[E: BaseEntity]:
    """
    Messages for actions response
    """

    @staticmethod
    def chapter_created_await_parsing_content(name: str = "") -> str:
        return _("Chapter {} created, please await to parsing content finished").format(name)
