# pylint: disable=duplicate-code
# pylint: disable=too-many-instance-attributes
"""
Base class for generators. Specifies the interface for generators.
"""
import typing

from classes.generated.definitions import ScriptAction, Repository, Environment
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
            self, windfile: WindFile, input_settings: InputSettings, output_settings: OutputSettings,
            metadata: PassMetadata
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

    def add_repository_urls_to_environment(self) -> None:
        """
        Some systems don't offer a way to access repository urls in the CI file.
        This is a workaround to make them available.
        :return: None
        """
        if self.windfile.repositories:
            for name in self.windfile.repositories:
                self.metadata.set(scope="repositories", value={})
                repository: Repository = self.windfile.repositories[name]
                variable_name: str = utils.get_target_environment_variable(target=self.input_settings.target,
                                                                           target_independent_name="REPOSITORY_URL",
                                                                           environment=self.environment)
                if self.windfile.environment is None:
                    self.windfile.environment = Environment(root={})
                repository_size: int = len(self.metadata.get(scope="repositories", key=None, subkey=None))
                if repository_size > 0:
                    variable_name += f"_{repository_size}"

                self.metadata.append(scope="repositories", key=name, subkey="url", value=variable_name)
                self.windfile.environment.root.root[variable_name] = repository.url

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
