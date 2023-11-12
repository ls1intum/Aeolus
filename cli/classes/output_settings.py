"""
Output settings for the CLI.
"""
# pylint: disable=too-many-arguments
from typing import Optional

from classes.ci_credentials import CICredentials
from classes.run_settings import RunSettings


class OutputSettings:
    """
    Output settings for the CLI.
    """

    verbose: bool = False
    debug: bool = False
    emoji: bool = False
    ci_credentials: Optional[CICredentials] = None
    run_settings: Optional[RunSettings] = None

    def __init__(
        self,
        verbose: bool = False,
        debug: bool = False,
        emoji: bool = False,
        ci_credentials: Optional[CICredentials] = None,
        run_settings: Optional[RunSettings] = None,
    ):
        self.verbose = verbose
        self.debug = debug
        self.emoji = emoji
        self.ci_credentials = ci_credentials
        self.run_settings = run_settings
