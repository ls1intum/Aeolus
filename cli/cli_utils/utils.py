import inspect
import os
import tempfile
import traceback as tb
import typing
from io import TextIOWrapper
from types import ModuleType
from typing import Optional

import pydantic
import yaml

from classes.generated.definitions import (
    Target,
    Docker,
    Environment,
    Dictionary,
    ScriptAction,
    FileAction,
    PlatformAction,
    TemplateAction,
)
from classes.generated.environment import EnvironmentSchema
from classes.generated.windfile import WindFile
from classes.output_settings import OutputSettings
from cli_utils import logger

T = typing.TypeVar("T")


def get_content_of(file: str) -> Optional[str]:
    """
    Returns the content of the given file.
    :param file: File to read, absolute path
    :return: Content of the given file
    """
    if not os.path.isfile(file):
        return None
    with open(file, "r", encoding="utf-8") as file_pointer:
        return file_pointer.read()


def execute_arbitrary_code(code: str, method: str, module_name: str = "module") -> None:
    """
    Executes the given code. This is a security risk, so use with caution.
    :param code: Code to execute
    :param method: Method to call
    :param module_name: Name of the module
    """
    # https://stackoverflow.com/a/19850183
    compiled = compile(code, "", "exec")
    module = ModuleType(module_name)
    # function = get_attr(module, method)
    exec(compiled, module.__dict__)  # pylint: disable=exec-used
    if hasattr(module, method):
        build(getattr(module, method))


def build(func: typing.Any) -> None:
    envs: dict = {
        "PYTHONPATH": "/home/runner/work/aeolus/aeolus",
    }
    possible_args: dict = {"envs": envs}

    function_parameters = inspect.signature(func).parameters
    defined_args: typing.List[str] = list(function_parameters)

    kwargs: dict[str, typing.Any] = possible_args.copy()

    for arg in possible_args:
        if arg not in defined_args:
            kwargs.pop(arg)

    def inner() -> None:
        print("This is aeolus speaking.")
        func(**kwargs)

    return inner()


def get_path_to_file(absolute_path: str, relative_path: str) -> str:
    """
    Returns the path of the given file.
    :param absolute_path: Absolute path of our point of view
    :param relative_path: Relative path of the file we need
    """
    return os.path.normpath(os.path.join(absolute_path, relative_path))


def file_exists(path: str, output_settings: OutputSettings) -> bool:
    """
    Checks if the given file exists.
    :param path: Path to the file
    :param output_settings: Output settings
    :return: True if the file exists, False otherwise
    """
    if not os.path.exists(path):
        logger.error(
            "❌ ",
            f"{path} does not exist",
            output_settings.emoji,
        )
        return False
    return True


def read_file(
    filetype: T,
    file: TextIOWrapper,
    output_settings: OutputSettings,
) -> Optional[T]:
    """
    Validates the given file. If the file is valid,
    the read object is returned.
    :param filetype: Filetype to validate
    :param file: File to read
    :param output_settings: OutputSettings
    :return: Validated object or None
    """
    try:
        typevalidator: pydantic.TypeAdapter = pydantic.TypeAdapter(filetype)
        content: str = file.read()
        validated: T = typevalidator.validate_python(yaml.safe_load(content))
        logger.info("✅ ", f"{file.name} is valid", output_settings.emoji)
        return validated
    except pydantic.ValidationError as validation_error:
        logger.info("❌ ", f"{file.name} is invalid", output_settings.emoji)
        logger.error("❌ ", str(validation_error), output_settings.emoji)
        if output_settings.debug:
            tb.print_exc()
        return None


def get_ci_environment(target: Target, output_settings: OutputSettings) -> Optional[EnvironmentSchema]:
    """
    Returns the CI environment for the given target.
    :param target: Target
    :param output_settings: OutputSettings
    :return: Environment
    """
    path: str = os.path.join(
        os.path.dirname(__file__), "..", "..", "schemas", "v0.0.1", "environment", f"{target.name}.yaml"
    )
    path = os.path.normpath(path)
    if file_exists(path, OutputSettings()):
        with open(path, "r", encoding="utf-8") as file:
            environment: type[EnvironmentSchema] | None = read_file(
                filetype=EnvironmentSchema, file=file, output_settings=output_settings
            )
            if isinstance(environment, EnvironmentSchema):
                return environment
    return None


def replace_environment_variables(
    environment: EnvironmentSchema, haystack: typing.List[str], reverse: bool = False
) -> list[str]:
    """
    Replaces the environment variables in the given list.
    :param environment: Environment variables
    :param haystack: List to replace
    :param reverse: Whether to reverse the replacement or not
    :return: Replaced list
    """
    result: typing.List[str] = []
    for item in haystack:
        for key, value in environment.__dict__.items():
            if reverse:
                value, key = key, value
            item = item.replace(key, value)
        result.append(item)
    return result


def replace_environment_variables_in_dict(
    environment: EnvironmentSchema,
    haystack: dict[typing.Any, typing.Any | str | float | bool | None],
    reverse: bool = False,
) -> dict[typing.Any, typing.Any | str | float | bool | None]:
    """
    Replaces the environment variables in the given list.
    :param environment: Environment variables
    :param haystack: List to replace
    :param reverse: Whether to reverse the replacement or not
    :return: Replaced list
    """
    result: dict[typing.Any, typing.Any | str | float | bool | None] = {}
    for item_key, item_value in haystack.items():
        for key, value in environment.__dict__.items():
            if reverse:
                value, key = key, value
            if isinstance(item_value, str):
                item_value = item_value.replace(key, value)
        result[item_key] = item_value
    return result


def get_target_environment_variable(
    target: Target, target_independent_name: str, environment: Optional[EnvironmentSchema]
) -> str:
    """
    Returns the environment variable name for the given target.
    :param target:
    :param target_independent_name:
    :param environment:
    :return:
    """
    if environment is None:
        environment = get_ci_environment(target=target, output_settings=OutputSettings())
    if environment is None:
        raise ValueError(f"No environment found for target {target.value}")
    return environment.__dict__[target_independent_name]


def replace_environment_variable(environment: EnvironmentSchema, haystack: str, reverse: bool = False) -> str:
    """
    Replaces the environment variables in the given list.
    :param environment: Environment variables
    :param haystack: List to replace
    :param reverse: Whether to reverse the replacement or not
    :return: Replaced string
    """
    return replace_environment_variables(environment=environment, haystack=[haystack], reverse=reverse)[0]


def replace_bamboo_environment_variable_with_aeolus(environment: EnvironmentSchema, haystack: str) -> str:
    """
    Replaces the bamboo environment variables with aeolus environment variables.
    :param environment: Environment variables
    :param haystack: String to replace
    :return: Replaced string
    """
    return replace_environment_variables(environment=environment, haystack=[haystack], reverse=True)[0]


def replace_bamboo_environment_variables_with_aeolus(
    environment: EnvironmentSchema, haystack: Optional[typing.List[str]]
) -> typing.List[str]:
    """
    Replaces the bamboo environment variables with aeolus environment variables.
    :param environment:
    :param haystack:
    :return:
    """
    if haystack is None:
        return []
    return replace_environment_variables(environment=environment, haystack=haystack, reverse=False)


def replace_env_variables_in_docker_config(
    environment: EnvironmentSchema, docker: Optional[Docker]
) -> Optional[Docker]:
    """
    Replaces the environment variables in the given docker config.
    :param environment: Environment variables
    :param docker: Docker config
    :return: None
    """
    if docker is None:
        return None
    docker.volumes = replace_bamboo_environment_variables_with_aeolus(environment=environment, haystack=docker.volumes)
    docker.parameters = replace_bamboo_environment_variables_with_aeolus(
        environment=environment, haystack=docker.parameters
    )
    return docker


def replace_environment_dictionary(environment: EnvironmentSchema, env: Optional[Environment]) -> Optional[Environment]:
    """
    Replaces the environment variables in the given environment dictionary.
    :param environment: Environment variables to replace
    :param env: Environment dictionary, containing the variables to replace
    :return: Environment dictionary with replaced variables
    """
    if env is None:
        return None
    dictionary: Dictionary = Dictionary(root={})
    for key, value in env.root.root.items():
        key = replace_environment_variable(environment=environment, haystack=key)
        if isinstance(value, str):
            value = replace_environment_variable(environment=environment, haystack=value)
        dictionary.root[key] = value
    return Environment(root=dictionary)


def replace_environment_variables_in_windfile(environment: EnvironmentSchema, windfile: WindFile) -> None:
    """
    Replaces the environment variables in the given windfile.
    :param environment:
    :param windfile:
    """
    windfile.metadata.docker = replace_env_variables_in_docker_config(
        environment=environment, docker=windfile.metadata.docker
    )
    windfile.environment = replace_environment_dictionary(environment=environment, env=windfile.environment)
    for action in windfile.actions:
        if isinstance(action.root, ScriptAction):
            action.root.script = replace_environment_variable(environment=environment, haystack=action.root.script)
        action.root.environment = replace_environment_dictionary(environment=environment, env=action.root.environment)
        if action.root.parameters:
            parameters: Dictionary = Dictionary(
                root=replace_environment_variables_in_dict(
                    environment=environment, haystack=action.root.parameters.root.root
                )
            )
            action.root.parameters.root = parameters


def combine_docker_config(windfile: WindFile, output_settings: OutputSettings) -> None:
    """
    Checks if all docker configurations are identical. If a bamboo plan is
    configured to be run in docker, the docker configuration can be equal
    in every action. So we can move the docker configuration to the metadata to make it easier to read.
    :param output_settings: OutputSettings
    :param windfile: Windfile to check
    """
    docker_configs: dict[str, Optional[Docker]] = {}
    for index, action in enumerate(windfile.actions):
        docker_configs[action.root.name] = windfile.actions[index].root.docker
    first: Optional[Docker] = list(docker_configs.values())[0]
    are_identical: bool = True
    for _, config in docker_configs.items():
        if first != config:
            logger.info("🚧", "Docker configurations are not identical", output_settings.emoji)
            are_identical = False
            break
    if are_identical:
        logger.info("🚀", "Docker configurations are identical", output_settings.emoji)
        windfile.metadata.docker = first
        for index, _ in enumerate(windfile.actions):
            windfile.actions[index].root.docker = None


def clean_up(windfile: WindFile, output_settings: OutputSettings) -> None:
    """
    Removes empty environment and parameters from the given windfile.
    :param windfile: Windfile to clean up
    :param output_settings: OutputSettings
    """
    combine_docker_config(windfile=windfile, output_settings=output_settings)
    for index, _ in enumerate(windfile.actions):
        root_action: FileAction | ScriptAction | PlatformAction | TemplateAction = windfile.actions[index].root
        if root_action.environment is not None and len(root_action.environment.root.root) == 0:
            root_action.environment = None
        if root_action.parameters is not None and len(root_action.parameters.root.root) == 0:
            root_action.parameters = None
        if root_action.excludeDuring is not None and len(root_action.excludeDuring) == 0:
            root_action.excludeDuring = None


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
