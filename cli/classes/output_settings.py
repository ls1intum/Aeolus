from typing import Optional

from classes.ci_credentials import CICredentials


class OutputSettings:
    """
    Output settings for the CLI.
    """

    verbose: bool = False
    debug: bool = False
    emoji: bool = False
    ci_credentials: Optional[CICredentials] = None

    def __init__(
        self,
        verbose: bool = False,
        debug: bool = False,
        emoji: bool = False,
        ci_credentials: Optional[CICredentials] = None,
    ):
        self.verbose = verbose
        self.debug = debug
        self.emoji = emoji
        self.ci_credentials = ci_credentials
