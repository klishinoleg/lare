from __future__ import annotations

from tortoise import fields

from .abstract import AbstractModel
from .mixins import TimestampMixin


class EventOutboxModel(AbstractModel, TimestampMixin):
    id = fields.IntField(primary_key=True)
    event_id = fields.CharField(max_length=64)
    event_type = fields.CharField(max_length=128)
    handler_group = fields.CharField(max_length=128)
    group_id = fields.CharField(max_length=255, null=True)
    pid = fields.CharField(max_length=255, null=True)
    status = fields.CharField(max_length=32, default="pending")
    attempts = fields.IntField(default=0)
    payload = fields.JSONField(default=dict)
    error_message = fields.TextField(null=True)

    class Meta:
        table = "event_outbox"
        unique_together = (("event_id", "handler_group"),)
