from io import TextIOWrapper


class InputSettings:
    """
    Settings for the input file.
    """

    file_path: str
    file: TextIOWrapper

    def __init__(self, file_path: str, file: TextIOWrapper):
        self.file_path = file_path
        self.file = file
