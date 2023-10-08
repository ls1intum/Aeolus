from typing import Optional


class OutputSettings:
    """
    Output settings for the CLI.
    """

    verbose: bool = False
    debug: bool = False
    emoji: bool = False
    ci_url: Optional[str] = None
    ci_token: Optional[str] = None

    def __init__(
        self,
        verbose: bool = False,
        debug: bool = False,
        emoji: bool = False,
        ci_url: Optional[str] = None,
        ci_token: Optional[str] = None,
    ):
        self.verbose = verbose
        self.debug = debug
        self.emoji = emoji
        self.ci_url = ci_url
        self.ci_token = ci_token
