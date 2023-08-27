import os
import typing
from types import ModuleType
from typing import Optional
import inspect

from classes.output_settings import OutputSettings
from utils import logger


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


def execute_arbitrary_code(
    code: str, method: str, module_name: str = "module"
) -> None:
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
    exec(compiled, module.__dict__) # pylint: disable=exec-used
    if hasattr(module, method):
        build(getattr(module, method))


def build(func: typing.Any) -> None:
    envs: dict = {
        "PYTHONPATH": "/home/runner/work/aeolus/aeolus",
    }
    possible_args: dict = {"envs": envs}

    function_parameters = inspect.signature(func).parameters
    defined_args: typing.List[str] = [key for key in function_parameters]

    kwargs: dict[str, typing.Any] = possible_args.copy()

    for arg in possible_args:
        if arg not in defined_args:
            kwargs.pop(arg)
    return None

    def inner():
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
            "❌",
            f"{logger} does not exist",
            output_settings.emoji,
        )
        return False
    return True
