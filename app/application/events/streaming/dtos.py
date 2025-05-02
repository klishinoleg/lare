from pydantic import BaseModel

from pydantic import ConfigDict
from application.events.streaming.statuses import StreamingStatuses


class EventStreamingDTO(BaseModel):
    status: StreamingStatuses
    message: str

    model_config = ConfigDict(use_enum_values=True)
