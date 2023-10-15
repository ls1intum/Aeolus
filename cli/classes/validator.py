import traceback
import typing
from typing import Optional

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
from classes.output_settings import OutputSettings
from classes.pass_settings import PassSettings
from utils import logger, utils

T = typing.TypeVar("T")


def has_external_actions(windfile: WindFile) -> bool:
    """
    Checks if the given windfile contains external actions.
    :param windfile: input windfile
    :return: True if the windfile contains external actions, False otherwise
    """
    for name in windfile.actions:
        action: Action = windfile.actions[name]
        if isinstance(action.root, ExternalAction):
            return True
    return False


def get_external_actions(
    windfile: typing.Optional[WindFile],
) -> typing.List[typing.Tuple[str, Action]]:
    """
    Returns a list of all external actions in the given windfile.
    :param windfile: WindFile to analyze
    :return: List of external actions in the given windfile
    """
    return get_actions_of_type(action_type=ExternalAction, windfile=windfile)


def get_platform_actions(
    windfile: Optional[WindFile],
) -> typing.List[typing.Tuple[str, Action]]:
    """
    Returns a list of all external actions in the given windfile.
    :param windfile: WindFile to analyze
    :return: List of external actions in the given windfile
    """
    return get_actions_of_type(action_type=PlatformAction, windfile=windfile)


def get_actions_of_type(
    action_type: T,
    windfile: typing.Optional[WindFile],
) -> typing.List[typing.Tuple[str, Action]]:
    """
    Returns a list of all file actions in the given windfile.
    :param action_type: Type of action to return
    :param windfile: Windfile to analyze
    :return: List of file actions in the given windfile
    """
    if not windfile:
        return []
    actions: typing.List[typing.Tuple[str, Action]] = []
    for name in windfile.actions:
        action: typing.Any = windfile.actions[name]
        if "root" in action.__dict__:
            # this allows handling of manually created actions during merging
            action = action.root
        if isinstance(action, action_type):  # type: ignore
            actions.append((name, action))
    return actions


def get_file_actions(
    windfile: typing.Optional[WindFile],
) -> typing.List[typing.Tuple[str, Action]]:
    """
    Returns a list of all file actions in the given windfile.
    :param windfile: Windfile to analyze
    :return: List of file actions in the given windfile
    """
    return get_actions_of_type(action_type=FileAction, windfile=windfile)


def get_internal_actions_with_names(
    windfile: typing.Optional[WindFile],
) -> typing.List[typing.Tuple[str, Action]]:
    """
    Returns a list of all internal actions in the given windfile with their names.
    :param windfile: Windfile to analyze
    :return: List of actions in the given windfile
    """
    return get_actions_of_type(action_type=InternalAction, windfile=windfile)


def get_actions(
    windfile: WindFile,
) -> typing.List[InternalAction | ExternalAction | FileAction | PlatformAction]:
    """
    Returns a list of all actions in the given windfile.
    :param windfile: Windfile to analyze
    :return: List of actions
    """
    actions: typing.List[InternalAction | ExternalAction | FileAction | PlatformAction] = []
    for name in windfile.actions:
        action: Action = windfile.actions[name]
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
    for name in windfile.actions:
        action: Action = windfile.actions[name]
        if isinstance(action.root, InternalAction):
            actions.append(action.root)
    return actions


def read_windfile(file: Optional[TextIOWrapper], output_settings: OutputSettings) -> Optional[WindFile]:
    """
    Validates the given file. If the file is valid, the windfile is returned.
    :param file: file to read
    :param output_settings: OutputSettings
    :return: Windfile or None
    """
    if file is None:
        return None
    # this shuts mypy up about the type
    windfile: type[WindFile] | None = utils.read_file(filetype=WindFile, file=file, output_settings=output_settings)
    if isinstance(windfile, WindFile):
        return windfile
    return None


def read_action_file(file: Optional[TextIOWrapper], output_settings: OutputSettings) -> Optional[ActionFile]:
    """
    Validates the given file. If the file is valid,
    the ActionFile is returned.
    :param file: file to validate
    :param output_settings: OutputSettings
    :return: ActionFile or None
    """
    # this shuts mypy up about the type
    if file is None:
        return None
    action_file: type[ActionFile] | None = utils.read_file(
        filetype=ActionFile, file=file, output_settings=output_settings
    )
    if isinstance(action_file, ActionFile):
        return action_file
    return None


class Validator(PassSettings):
    def validate_action_file(self) -> Optional[ActionFile]:
        """
        Validates the given actionfile. If the file is valid, the
        actionfile is returned.
        :return:
        """
        logger.info("🌬️", "Validating action", self.output_settings.emoji)
        action: Optional[ActionFile] = read_action_file(
            file=self.input_settings.file, output_settings=self.output_settings
        )
        return action

    def validate_wind_file(self) -> Optional[WindFile]:
        """
        Validates the given windfile. If the file is valid,
        the windfile is returned.
        :return: Windfile or None
        """
        logger.info("🌬️", "Validating windfile", self.output_settings.emoji)
        windfile: Optional[WindFile] = read_windfile(
            file=self.input_settings.file,
            output_settings=self.output_settings,
        )
        if windfile and has_external_actions(windfile):
            logger.info(
                "🌍",
                "This windfile contains external actions.",
                self.output_settings.emoji,
            )
        return windfile
