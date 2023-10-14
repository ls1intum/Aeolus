# pylint: disable=duplicate-code
import typing

from classes.generated.definitions import InternalAction
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.pass_metadata import PassMetadata
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
    final_result: typing.Optional[str]

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

    def add_line(self, indentation: int, line: str) -> None:
        """
        Add a line to the result.
        :param indentation: indentation level
        :param line: line to add
        """
        self.result.append(" " * indentation + line)

    def has_always_actions(self) -> bool:
        """
        Check if there are always actions in the windfile.
        """
        for _, action in self.windfile.actions.items():
            if action.root.run_always:
                return True
        return False

    def handle_step(self, name: str, step: InternalAction, call: bool) -> None:
        """
        Translate a step into a CI action.
        :param name: name of the step to handle
        :param step: step to translate
        :param call: whether to call the step or not
        :return: CI action
        """
        raise NotImplementedError("handle_step() not implemented")

    def check(self, content: str) -> bool:
        """
        Check the generated CI file for syntax errors.
        """
        raise NotImplementedError("check_syntax() not implemented")

    def generate(self) -> str:
        """
        Generate the CI file.
        """
        self.final_result = "\n".join(self.result)
        return self.final_result

    def run(self, job_id: str) -> None:
        """
        Run the resulting script.
        """
        raise NotImplementedError("run() not implemented")
