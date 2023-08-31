import tempfile
import typing


class TemporaryFileWithContent:
    """
    A temporary file with content.
    """

    file: typing.Any

    def __init__(self, content: str):
        # pylint: disable=consider-using-with
        self.file = tempfile.NamedTemporaryFile(mode="w+")
        self.file.write(content)
        self.file.seek(0)

    def __enter__(self) -> typing.Any:
        return self.file.__enter__()

    def __exit__(self, exc_type: typing.Any, exc_value: typing.Any, traceback: typing.Any) -> None:
        self.file.__exit__(exc_type, exc_value, traceback)
