import typing
from typing import Optional

import argparse
import pydantic
import yaml
from io import TextIOWrapper

from classes.generated.action import Actionfile
from classes.generated.windfile import (
    Windfile,
    Action as WindAction,
    ExternalAction,
    InternalAction,
)

from typing import TypeVar

from commands.subcommand import Subcommand


def contains_external_actions(windfile: Windfile) -> bool:
    """
    Checks if the given windfile contains external actions.
    :param windfile: input windfile
    :return: True if the windfile contains external actions, False otherwise
    """
    for name in windfile.jobs:
        action: WindAction = windfile.jobs[name]
        if isinstance(action.root, ExternalAction):
            return True
    return False


def get_external_actions(windfile: Windfile) -> typing.List[ExternalAction]:
    """
    Returns a list of all external actions in the given windfile.
    :param windfile:
    :return:
    """
    actions: typing.List[ExternalAction] = []
    for name in windfile.jobs:
        action: WindAction = windfile.jobs[name]
        if isinstance(action.root, ExternalAction):
            actions.append(action.root)
    return actions


def get_actions(
    windfile: Windfile,
) -> typing.List[InternalAction | ExternalAction]:
    actions: typing.List[InternalAction | ExternalAction] = []
    """
    Returns a list of all actions in the given windfile.
    :param windfile: Windfile to analyze
    :return: List of actions
    """
    for name in windfile.jobs:
        action: WindAction = windfile.jobs[name]
        if isinstance(action.root, InternalAction):
            actions.append(action.root)
        elif isinstance(action.root, ExternalAction):
            actions.append(action.root)
    return actions


def get_internal_actions(windfile: Windfile) -> typing.List[InternalAction]:
    """
    Returns a list of all internal actions in the given windfile.
    :param windfile:
    :return:
    """
    actions: typing.List[InternalAction] = []
    for name in windfile.jobs:
        action: WindAction = windfile.jobs[name]
        if isinstance(action.root, InternalAction):
            actions.append(action.root)
    return actions


class Validator(Subcommand):
    T = TypeVar("T")

    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser):
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
        )

    def read_file(self, filetype: T, path: TextIOWrapper) -> Optional[T]:
        try:
            typevalidator: pydantic.TypeAdapter = pydantic.TypeAdapter(filetype)
            content: str = path.read()
            file: Validator.T = typevalidator.validate_python(yaml.safe_load(content))
            if file and self.args.verbose:
                print(f"✅ {self.args.input.name} is valid")
            return file
        except pydantic.ValidationError as validation_error:
            if self.args.verbose:
                print(f"❌ {self.args.input.name} is invalid")
            print(validation_error)
            return None

    def read_windfile(self, path: TextIOWrapper) -> Optional[Windfile]:
        """
        Validates the given file. If the file is valid, the windfile is returned.
        :param path: path to input
        :return: Windfile or None
        """
        # this shuts mypy up about the type
        windfile: type[Windfile] | None = self.read_file(filetype=Windfile, path=path)
        if isinstance(windfile, Windfile):
            return windfile
        return None

    def read_actionfile(self, path: TextIOWrapper) -> Optional[Actionfile]:
        """
        Validates the given file. If the file is valid, the Actionfile is returned.
        :param path: path to input
        :return: Actionfile or None
        """
        # this shuts mypy up about the type
        action_file: type[Actionfile] | None = self.read_file(filetype=Actionfile, path=path)
        if isinstance(action_file, Actionfile):
            return action_file
        return None

    def validate(self) -> Actionfile | Windfile | None:
        """
        Validates the given file. If the file is valid, the read object is returned.
        If the file is invalid, None is returned.
        :return: Actionfile or Windfile or None
        """
        if self.args.wind:
            windfile: Optional[Windfile] = self.read_windfile(self.args.input)
            if self.args.verbose:
                if windfile and contains_external_actions(windfile):
                    print("🌍This windfile contains external actions.")
            return windfile
        elif self.args.action:
            action: Optional[Actionfile] = self.read_actionfile(self.args.input)
            return action
        return None
