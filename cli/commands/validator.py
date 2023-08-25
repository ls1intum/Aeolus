import traceback
import typing
from typing import Optional

import argparse
from io import TextIOWrapper
import pydantic
import yaml


from classes.generated.actionfile import ActionFile
from classes.generated.definitions import (
    Action,
    ExternalAction,
    FileAction,
    InternalAction,
    PlatformAction,
)
from classes.generated.windfile import WindFile
from commands.subcommand import Subcommand


T = typing.TypeVar("T")


def has_external_actions(windfile: WindFile) -> bool:
    """
    Checks if the given windfile contains external actions.
    :param windfile: input windfile
    :return: True if the windfile contains external actions, False otherwise
    """
    for name in windfile.jobs:
        action: Action = windfile.jobs[name]
        if isinstance(action.root, ExternalAction):
            return True
    return False


def get_external_actions(
    windfile: Optional[WindFile],
) -> typing.List[typing.Tuple[str, Action]]:
    """
    Returns a list of all external actions in the given windfile.
    :param windfile: WindFile to analyze
    :return: List of external actions in the given windfile
    """
    return get_actions_of_type(actiontype=ExternalAction, windfile=windfile)


def get_platform_actions(
    windfile: Optional[WindFile],
) -> typing.List[typing.Tuple[str, Action]]:
    """
    Returns a list of all external actions in the given windfile.
    :param windfile: WindFile to analyze
    :return: List of external actions in the given windfile
    """
    return get_actions_of_type(actiontype=PlatformAction, windfile=windfile)


def get_actions_of_type(
    actiontype: T,
    windfile: Optional[WindFile],
) -> typing.List[typing.Tuple[str, Action]]:
    """
    Returns a list of all file actions in the given windfile.
    :param actiontype: Type of action to return
    :param windfile: Windfile to analyze
    :return: List of file actions in the given windfile
    """
    if not windfile:
        return []
    actions: typing.List[typing.Tuple[str, Action]] = []
    for name in windfile.jobs:
        action: typing.Any = windfile.jobs[name]
        if "root" in action.__dict__:
            # this allows handling of manually created actions during merging
            action = action.root
        if isinstance(action, actiontype):  # type: ignore
            actions.append((name, action))
    return actions


def get_file_actions(
    windfile: Optional[WindFile],
) -> typing.List[typing.Tuple[str, Action]]:
    """
    Returns a list of all file actions in the given windfile.
    :param windfile: Windfile to analyze
    :return: List of file actions in the given windfile
    """
    return get_actions_of_type(actiontype=FileAction, windfile=windfile)


def get_actions(
    windfile: WindFile,
) -> typing.List[
    InternalAction | ExternalAction | FileAction | PlatformAction
]:
    """
    Returns a list of all actions in the given windfile.
    :param windfile: Windfile to analyze
    :return: List of actions
    """
    actions: typing.List[
        InternalAction | ExternalAction | FileAction | PlatformAction
    ] = []
    for name in windfile.jobs:
        action: Action = windfile.jobs[name]
        if isinstance(action.root, InternalAction):
            actions.append(action.root)
        elif isinstance(action.root, ExternalAction):
            actions.append(action.root)
        elif isinstance(action.root, FileAction):
            actions.append(action.root)
        elif isinstance(action.root, PlatformAction):
            actions.append(action.root)
    return actions


def get_internal_actions(windfile: WindFile) -> typing.List[InternalAction]:
    """
    Returns a list of all internal actions in the given windfile.
    :param windfile:
    :return:
    """
    actions: typing.List[InternalAction] = []
    for name in windfile.jobs:
        action: Action = windfile.jobs[name]
        if isinstance(action.root, InternalAction):
            actions.append(action.root)
    return actions


def read_file(
    filetype: T,
    path: TextIOWrapper,
    verbose: bool = False,
    debug: bool = False,
) -> Optional[T]:
    """
    Validates the given file. If the file is valid,
    the read object is returned.
    :param filetype: Filetype to validate
    :param path: Path to input
    :param verbose: Print more output
    :param debug: Print debug output
    :return:
    """
    try:
        typevalidator: pydantic.TypeAdapter = pydantic.TypeAdapter(filetype)
        content: str = path.read()
        file: T = typevalidator.validate_python(yaml.safe_load(content))
        if file and verbose:
            print(f"✅ {path.name} is valid")
        return file
    except pydantic.ValidationError as validation_error:
        if verbose:
            print(f"❌ {path.name} is invalid")
        print(validation_error)
        if debug:
            traceback.print_exc()
        return None


def read_windfile(
    path: TextIOWrapper, verbose: bool = False, debug: bool = False
) -> Optional[WindFile]:
    """
    Validates the given file. If the file is valid, the windfile is returned.
    :param debug:  debug mode
    :param verbose: more output
    :param path: path to input
    :return: Windfile or None
    """
    # this shuts mypy up about the type
    windfile: type[WindFile] | None = read_file(
        filetype=WindFile, path=path, verbose=verbose, debug=debug
    )
    if isinstance(windfile, WindFile):
        return windfile
    return None


def read_action_file(
    path: TextIOWrapper, verbose: bool = False, debug: bool = False
) -> Optional[ActionFile]:
    """
    Validates the given file. If the file is valid, the ActionFile is returned.
    :param path: path to input
    :param verbose: more output
    :param debug: debug mode
    :return: ActionFile or None
    """
    # this shuts mypy up about the type
    action_file: type[ActionFile] | None = read_file(
        filetype=ActionFile, path=path, verbose=verbose, debug=debug
    )
    if isinstance(action_file, ActionFile):
        return action_file
    return None


class Validator(Subcommand):
    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--wind", "-w", help="Validate windfile.", action="store_true"
        )
        parser.add_argument(
            "--action", "-a", help="Validate action.", action="store_true"
        )
        parser.add_argument(
            "--input",
            "-i",
            help="Input file to read from",
            default="windfile.yaml",
            required=True,
            type=open,
        )  # pylint: disable=duplicate-code

    def validate(self) -> ActionFile | WindFile | None:
        """
        Validates the given file. If the file is valid,
        the read object is returned.
        If the file is invalid, None is returned.
        :return: ActionFile or WindFile or None
        """
        if self.args.wind:
            if self.args.verbose:
                print("🌬️ Validating windfile")
            windfile: Optional[WindFile] = read_windfile(
                path=self.args.input,
                verbose=self.args.verbose,
                debug=self.args.debug,
            )
            if self.args.verbose:
                if windfile and has_external_actions(windfile):
                    print("🌍This windfile contains external actions.")
            return windfile
        if self.args.action:
            if self.args.verbose:
                print("🌬️ Validating action")
            action: Optional[ActionFile] = read_action_file(
                path=self.args.input,
                verbose=self.args.verbose,
                debug=self.args.debug,
            )
            return action
        return None
