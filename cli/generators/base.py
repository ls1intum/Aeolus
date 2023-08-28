import typing

from classes.generated.definitions import InternalAction
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.metadata import PassMetadata
from classes.output_settings import OutputSettings


class BaseGenerator:
    """
    Base class for generators. Specifies the interface for generators.
    """

    windfile: WindFile
    input_settings: InputSettings
    output_settings: OutputSettings
    metadata: PassMetadata
    result: typing.List[str]

    def __init__(
        self,
        windfile: WindFile,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        metadata: PassMetadata,
    ):
        self.windfile = windfile
        self.input_settings = input_settings
        self.output_settings = output_settings
        self.metadata = metadata
        self.result = []

    def handle_step(self, name: str, step: InternalAction) -> None:
        """
        Translate a step into a CI action.
        :param name: name of the step to handle
        :param step: step to translate
        :return: CI action
        """
        raise NotImplementedError("handle_step() not implemented")
        return None

    def generate(self) -> str:
        """
        Generate the CI file.
        """
        return "\n".join(self.result)
