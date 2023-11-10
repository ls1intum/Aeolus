# pylint: disable=duplicate-code
# pylint: disable=too-many-instance-attributes
import typing

from classes.generated.definitions import ScriptAction
from classes.generated.environment import EnvironmentSchema
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.pass_metadata import PassMetadata
from classes.output_settings import OutputSettings
from cli_utils import utils


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
    environment: EnvironmentSchema
    key: typing.Optional[str]

    def __init__(
        self, windfile: WindFile, input_settings: InputSettings, output_settings: OutputSettings, metadata: PassMetadata
    ):
        self.windfile = windfile
        self.input_settings = input_settings
        self.output_settings = output_settings
        self.metadata = metadata
        self.result = []
        if input_settings.target is None:
            raise ValueError("No target specified")
        env: typing.Optional[EnvironmentSchema] = utils.get_ci_environment(
            target=input_settings.target, output_settings=output_settings
        )
        if env is None:
            raise ValueError(f"No environment found for target {input_settings.target.value}")
        self.environment = env
        self.key = None

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
        for action in self.windfile.actions:
            if action.root.runAlways:
                return True
        return False

    def handle_step(self, name: str, step: ScriptAction, call: bool) -> None:
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
