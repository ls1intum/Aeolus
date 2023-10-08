class CICredentials:
    """
    Class to store CI credentials
    """
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token

    url: str
    token: str
