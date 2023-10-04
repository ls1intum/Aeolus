from io import TextIOWrapper
from typing import Optional


class InputSettings:
    """
    Settings for the input file.
    """

    file_path: str
    file: Optional[TextIOWrapper]

    def __init__(self, file_path: str, file: Optional[TextIOWrapper] = None):
        self.file_path = file_path
        self.file = file
