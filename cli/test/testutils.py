import tempfile


class TemporaryFileWithContent:
    """
    A temporary file with content.
    """

    file: tempfile.NamedTemporaryFile

    def __init__(self, content: str):
        self.file = tempfile.NamedTemporaryFile(mode="w+")
        self.file.write(content)
        self.file.seek(0)

    def __enter__(self):
        return self.file.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.__exit__(exc_type, exc_value, traceback)
