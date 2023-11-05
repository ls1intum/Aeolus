from typing import Any, Optional

from pydantic import BaseModel


class PublishPayload(BaseModel):
    windfile: str
    url: str
    username: Optional[str]
    token: str

    def __init__(self, **data: Any):
        super().__init__(**data)
