"""
Run settings for the CI job.
"""
from classes.generated.definitions import Lifecycle


class RunSettings:
    """
    Run settings for the CI job.
    """

    def __init__(self, stage: Lifecycle = Lifecycle.preparation):
        self.stage = stage

    stage: Lifecycle
