class OutputSettings:
    """
    Output settings for the CLI.
    """

    verbose: bool = False
    debug: bool = False
    emoji: bool = False

    def __init__(self, verbose: bool = False, debug: bool = False, emoji: bool = False):
        self.verbose = verbose
        self.debug = debug
        self.emoji = emoji
