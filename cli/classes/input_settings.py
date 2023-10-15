from io import TextIOWrapper
from typing import Optional

from classes.generated.definitions import Target


class InputSettings:
    """
    Settings for the input file.
    """

    file_path: str
    file: Optional[TextIOWrapper]
    target: Optional[Target]

    def __init__(self, file_path: str, target: Optional[Target] = None, file: Optional[TextIOWrapper] = None):
        self.file_path = file_path
        self.target = target
        self.file = file
