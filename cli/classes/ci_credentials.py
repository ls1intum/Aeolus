from typing import Optional


class CICredentials:
    """
    Class to store CI credentials
    """

    def __init__(self, url: str, username: Optional[str], token: str):
        self.url = url
        self.username = username
        self.token = token

    url: str
    username: Optional[str]
    token: str
