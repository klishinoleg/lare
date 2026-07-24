from pydantic import BaseModel, Field

from pydantic import ConfigDict

from application.events.event_types import EventTypes
from application.events.streaming.statuses import StreamingStatuses


class EventStreamingDTO[ET: EventTypes](BaseModel):
    status: StreamingStatuses = Field(..., description="Status of the event")
    event_type: ET | None = Field(None, description="Pending status of the event")
    message: str = Field(default="", description="Message of the status")

    model_config = ConfigDict(use_enum_values=True)
