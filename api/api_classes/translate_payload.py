from typing import Optional

from pydantic import BaseModel


class TranslatePayload(BaseModel):
    url: str
    username: Optional[str]
    token: str
