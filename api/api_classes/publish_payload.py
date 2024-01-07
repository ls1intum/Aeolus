from typing import Optional

from pydantic import BaseModel


class PublishPayload(BaseModel):
    windfile: str
    url: Optional[str]
    username: Optional[str]
    token: Optional[str]
