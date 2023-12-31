# pylint: disable=duplicate-code
# pylint: disable=too-many-instance-attributes
"""
Base class for generators. Specifies the interface for generators.
"""
import typing

from classes.generated.definitions import ScriptAction, Repository, Environment, Dictionary, Result
from classes.generated.environment import EnvironmentSchema
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.pass_metadata import PassMetadata
from cli_utils import utils


class BaseGenerator:
    """
    Base class for generators. Specifies the interface for generators.
    """

    windfile: WindFile
    input_settings: InputSettings
    output_settings: OutputSettings
    metadata: PassMetadata
    result: str
    final_result: typing.Optional[str]
    environment: EnvironmentSchema
    key: typing.Optional[str]
    before_results: dict[str, list[Result]] = {}
    results: dict[str, list[Result]] = {}
    after_results: dict[str, list[Result]] = {}
    needs_lifecycle_parameter: bool = False
    has_multiple_steps: bool = False
    needs_subshells: bool = False

    def __init__(
        self, windfile: WindFile, input_settings: InputSettings, output_settings: OutputSettings, metadata: PassMetadata
    ):
        self.windfile = windfile
        self.input_settings = input_settings
        self.output_settings = output_settings
        self.metadata = metadata
        self.result = ""
        if input_settings.target is None:
            raise ValueError("No target specified")
        env: typing.Optional[EnvironmentSchema] = utils.get_ci_environment(
            target=input_settings.target, output_settings=output_settings
        )
        if env is None:
            raise ValueError(f"No environment found for target {input_settings.target.value}")
        self.environment = env
        self.results = {}
        self.before_results = {}
        self.after_results = {}
        self.key = None
        self.has_multiple_steps = (
            len(
                [
                    action
                    for action in self.windfile.actions
                    if action.root.platform == self.input_settings.target or not action.root.platform
                ]
            )
            > 1
        )
        self.needs_lifecycle_parameter = self.__needs_lifecycle_parameter()
        self.needs_subshells = self.has_multiple_steps

    def add_repository_urls_to_environment(self) -> None:
        """
        Some systems don't offer a way to access repository urls in the CI file.
        This is a workaround to make them available.
        :return: None
        """
        if self.windfile.repositories and self.input_settings.target:
            self.metadata.set(scope="repositories", value={})
            for name in self.windfile.repositories:
                repository: Repository = self.windfile.repositories[name]
                variable_name: str = utils.get_target_environment_variable(
                    target=self.input_settings.target,
                    target_independent_name="REPOSITORY_URL",
                    environment=self.environment,
                )
                if self.windfile.environment is None:
                    self.windfile.environment = Environment(root=Dictionary(root={}))
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
            if action.root.runAlways and (
                action.root.platform == self.input_settings.target or not action.root.platform
            ):
                return True
        return False

    def has_results(self) -> bool:
        """
        Check if there are results in the windfile.
        """
        if self.before_results or self.after_results:
            return True
        for action in self.windfile.actions:
            if action.root.results and (action.root.platform == self.input_settings.target or not action.root.platform):
                return True
        return False

    def add_result(self, workdir: str, result: Result) -> None:
        """
        Add a result to the results dictionary.
        """
        if workdir not in self.results:
            self.results[workdir] = []
        self.results[workdir].append(result)

    def __needs_lifecycle_parameter(self) -> bool:
        """
        Check if the CI system needs lifecycle parameters.
        """
        for action in self.windfile.actions:
            if action.root.excludeDuring and (
                action.root.platform == self.input_settings.target or not action.root.platform
            ):
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
        return self.result

    def run(self, job_id: str) -> None:
        """
        Run the resulting script.
        """
        raise NotImplementedError("run() not implemented")
