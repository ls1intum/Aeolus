from typing import Optional

from pydantic import BaseModel


class PublishPayload(BaseModel):
    windfile: str
    url: str
    username: Optional[str]
    token: str
