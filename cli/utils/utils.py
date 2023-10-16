import os
import traceback
import typing
from io import TextIOWrapper
from types import ModuleType
from typing import Optional
import inspect

import pydantic
import yaml

from classes.generated.definitions import Target, Docker, WindfileMetadata, Environment, Dictionary, InternalAction
from classes.generated.environment import EnvironmentSchema
from classes.generated.windfile import WindFile
from classes.output_settings import OutputSettings
from utils import logger

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
            traceback.print_exc()
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


def replace_env_variables_in_docker_config(environment: EnvironmentSchema, docker: Optional[Docker]) -> Optional[Docker]:
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


def replace_environment_variables_in_windfile(environment: EnvironmentSchema, windfile: WindFile) -> None:
    """
    Replaces the environment variables in the given windfile.
    :param environment:
    :param windfile:
    """
    metadata: WindfileMetadata = windfile.metadata
    windfile.metadata.docker = replace_env_variables_in_docker_config(environment=environment, docker=windfile.metadata.docker)
    if windfile.environment is not None:
        dictionary: Dictionary = Dictionary()
        for key, value in windfile.environment.root.root.items():
            dictionary[
                replace_environment_variable(environment=environment, haystack=key)
            ] = replace_environment_variable(environment=environment, haystack=value)
        metadata.environment = Environment(root=dictionary)
    for name, action in windfile.actions.items():
        if isinstance(action.root, InternalAction):
            action.root.script = replace_environment_variable(environment=environment, haystack=action.root.script)
        if action.root.environment is not None:
            dictionary: Dictionary = Dictionary()
            for key, value in action.root.environment.root.root.items():
                dictionary[
                    replace_environment_variable(environment=environment, haystack=key)
                ] = replace_environment_variable(environment=environment, haystack=value)
            action.root.environment = Environment(root=dictionary)
