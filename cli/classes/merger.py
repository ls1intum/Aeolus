import os
import traceback
import typing
from typing import List, Optional

import yaml

from classes.generated.actionfile import ActionFile, Step
from classes.generated.definitions import (
    Parameters,
    Action,
    Dictionary,
    Lifecycle,
    Environment,
    PlatformAction,
    FileAction,
    ExternalAction,
    InternalAction,
)
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.metadata import PassMetadata
from classes.output_settings import OutputSettings
from classes.pass_settings import PassSettings
from classes.validator import (
    read_action_file,
    get_platform_actions,
    get_external_actions,
    get_file_actions,
    Validator,
)
from utils import logger
from utils.utils import get_content_of, get_path_to_file, file_exists


def merge_parameters(parameters: Parameters | None, action: Action) -> None:
    """
    Merges the given parameters into the parameters of the action.
    :param parameters: Parameters to merge into the action
    :param action: Action to merge the parameters into
    """
    if parameters:
        param_list: dict = (
            action.root.parameters.root.root if action.root.parameters else {}
        )
        param_list.update(parameters.root.root)
        action.root.parameters = Parameters(root=Dictionary(root=param_list))


def merge_environment(environment: Environment | None, action: Action) -> None:
    """
    Merges the given environment variables into the environment variables of the action.
    :param environment: environment to merge
    :param action: action to merge the environment variables into
    """
    if environment:
        env_list: dict = {}
        if action.root.environment:
            env_list = action.root.environment.root.root
        env_list.update(environment.root.root)
        action.root.environment = Environment(root=Dictionary(root=env_list))


def merge_lifecycle(lifecycle: List[Lifecycle] | None, action: Action) -> None:
    """
    Creates a superset of the given lifecycle items and the lifecycle of the action and adds it to the action.
    :param lifecycle: lifecycle items to add
    :param action: action to add the lifecycle items to
    """
    if lifecycle:
        lifecycle_list: list = (
            action.root.excludeDuring if action.root.excludeDuring else []
        )
        lifecycle_list.extend(lifecycle)
        action.root.excludeDuring = lifecycle_list


class Merger(PassSettings):
    """
    Merger class. Merges external actions into the windfile to simplify the generation process.
    """

    def __init__(
        self,
        windfile: Optional[WindFile],
        input_settings: InputSettings,
        output_settings: OutputSettings,
        metadata: PassMetadata,
    ):
        super().__init__(
            windfile=windfile,
            input_settings=input_settings,
            output_settings=output_settings,
            metadata=metadata,
        )
        if not windfile:
            validator: Validator = Validator(
                output_settings=output_settings, input_settings=input_settings
            )
            validated: Optional[WindFile] = validator.validate_wind_file()
            if validated:
                self.windfile = validated
        else:
            self.windfile = windfile

    def merge_file_actions(self) -> bool:
        """
        Merges the file actions into the windfile.
        :return: True if the file actions could be merged, False otherwise
        """
        logger.info("📄", "Merging file actions", self.output_settings.emoji)
        actions: List[tuple[str, Action]] = get_file_actions(self.windfile)
        logger.info(
            "📄",
            f"found {len(actions)} file actions",
            self.output_settings.emoji,
        )
        self.set_original_types(
            names=[action_tuple[0] for action_tuple in actions], key="file"
        )
        return self.traverse_external_actions(external_actions=actions)

    def merge_external_actions(self) -> bool:
        """
        Merges the external actions into the windfile.
        :return: True if the external actions could be merged, False otherwise
        """
        logger.info(
            "🌍", "Merging external actions", self.output_settings.emoji
        )
        actions: list[tuple[str, Action]] = get_external_actions(self.windfile)
        logger.info(
            "🌍",
            f"found {len(actions)} external actions",
            self.output_settings.emoji,
        )
        return self.traverse_external_actions(external_actions=actions)

    def set_original_types(self, names: List[str], key: str) -> None:
        """
        Sets the original type of the given actions to the given key.
        :param names: Names of the actions
        :param key: Key to set the original type to
        :return: None
        """
        for name in names:
            self.metadata.append(
                scope="actions",
                key=name,
                subkey="original_type",
                value=key,
            )

    def merge_platform_actions(self) -> bool:
        """
        Merges the platform actions into the windfile.
        :return: True if the platform actions could be merged, False otherwise
        """
        logger.info(
            "🚉", "Merging platform actions", self.output_settings.emoji
        )
        actions: list[tuple[str, Action]] = get_platform_actions(self.windfile)
        logger.info(
            "🚉",
            f"found {len(actions)} platform actions",
            self.output_settings.emoji,
        )
        self.set_original_types(
            names=[action_tuple[0] for action_tuple in actions], key="platform"
        )
        return self.traverse_external_actions(external_actions=actions)

    # def inline_external_actions(
    #     self, external_actions: List[typing.Tuple[str, ExternalAction]]
    # ) -> bool:
    #     """
    #     Inlines the given external actions from an Actionfile into the windfile.
    #     :param external_actions: list of external actions to be inlined
    #     :return: True if the external actions could be inlined, False otherwise
    #     """
    #     if not self.windfile:
    #         logger.error(
    #             "❌",
    #             "No windfile found. Aborting.",
    #             self.output_settings.emoji,
    #         )
    #         return False
    #     for external_action_tuple in external_actions:
    #         external_action_name: str = external_action_tuple[0]
    #         external_action: ExternalAction = external_action_tuple[1]
    #         file: Optional[str] = external_action.use
    #         absolute_path: str = os.path.join(
    #             self.input_settings.file_path, file if file else ""
    #         )
    #         action_file: Optional[ActionFile] = self.read_external_action_file(
    #             path=absolute_path
    #         )
    #         if not action_file:
    #             continue
    #         for name in action_file.steps:
    #             internals: Step = action_file.steps[name]
    #             new_name: str = f"{external_action_name}_{name}"
    #             if not isinstance(
    #                 internals.root, InternalAction
    #             ) and not isinstance(internals.root, PlatformAction):
    #                 logger.info(
    #                     "❌",
    #                     f"Unsupported action type {type(internals.root)}",
    #                     self.output_settings.emoji,
    #                 )
    #                 logger.error(
    #                     "❌",
    #                     "Only internal and platform actions are supported",
    #                     self.output_settings.emoji,
    #                 )
    #                 return False
    #             script: str | None = None
    #             if isinstance(internals.root, InternalAction):
    #                 script = internals.root.script
    #                 self.metadata.append(
    #                     scope="actions",
    #                     key=external_action_name,
    #                     subkey="orignal_type",
    #                     value='internal',
    #                 )
    #             if isinstance(internals.root, PlatformAction):
    #                 script = get_content_of(internals.root.file)
    #                 self.metadata.append(
    #                     scope="actions",
    #                     key=external_action_name,
    #                     subkey="orignal_type",
    #                     value='platform',
    #                 )
    #
    #             if not script:
    #                 logger.error(
    #                     "❌",
    #                     f"could not read script of {name}",
    #                     self.output_settings.emoji,
    #                 )
    #                 return False
    #
    #             internal: Action = Action(
    #                 root=InternalAction(
    #                     script=script,
    #                     excludeDuring=internals.root.excludeDuring,
    #                     environment=internals.root.environment,
    #                     parameters=internals.root.parameters,
    #                     platform=internals.root.platform,
    #                 )
    #             )
    #             self.metadata.append(
    #                 scope="actions",
    #                 key=external_action_name,
    #                 subkey="original_name",
    #                 value=new_name,
    #             )
    #             self.windfile.jobs[new_name] = internal
    #     return True

    def read_external_action_file(self, path: str) -> Optional[ActionFile]:
        """
        Reads the given file and returns an ActionFile object.
        :param path: Path to the file to read
        :return: ActionFile object or None if the file could not be read
        """
        if not os.path.exists(path):
            logger.error(
                "❌", f"{path} does not exist", self.output_settings.emoji
            )
            return None
        with open(path, encoding="utf-8") as file:
            return read_action_file(
                file=file, output_settings=self.output_settings
            )

    def traverse_external_actions(
        self,
        external_actions: List[typing.Tuple[str, Action]],
    ) -> bool:
        """
        Traverses the given list of external actions and inlines them into the windfile.
        :param external_actions: list of external actions
        :return:
        """
        if not self.windfile:
            logger.error(
                "❌",
                "No windfile found. Aborting.",
                self.output_settings.emoji,
            )
            return False
        for entry in external_actions:
            try:
                name: str = entry[0]
                action: Action = entry[1]
                path: Optional[str] = None
                if isinstance(action, FileAction) or isinstance(
                    action, PlatformAction
                ):
                    path = action.file
                elif isinstance(action, ExternalAction):
                    path = action.use
                if not path:
                    logger.error(
                        "❌", f"{path} not found", self.output_settings.emoji
                    )
                    return False
                converted: Optional[
                    typing.Tuple[
                        typing.List[str],
                        typing.List[Action],
                    ]
                ] = self.convert_external_action_to_internal(
                    external_file=path,
                    action=action,
                )
                if not converted:
                    logger.error(
                        "❌",
                        f"{path} could not be converted",
                        self.output_settings.emoji,
                    )
                    return False
                logger.info(
                    "📄 ", f"{path} converted", self.output_settings.emoji
                )

                if len(converted[0]) == 1:
                    # found no other way to do this
                    self.windfile.jobs[name] = converted[1][0]  # type: ignore
                    self.metadata.append(
                        scope="actions",
                        key=name,
                        subkey="original_name",
                        value=name,
                    )
                    self.metadata.append(
                        scope="actions",
                        key=name,
                        subkey="original_type",
                        value=converted[0][0],
                    )
                else:
                    self.inline_actions(name=name, actions=converted)
            # ignore pylint: disable=broad-except
            except Exception as exception:
                logger.error("❌", f"{exception}", self.output_settings.emoji)
                if self.output_settings.debug:
                    traceback.print_exc()
        return True

    def inline_actions(
        self,
        name: str,
        actions: typing.Tuple[
            typing.List[str],
            typing.List[Action],
        ],
    ) -> None:
        """
        Inlines the given actions into the windfile.
        :param name: Name of the action
        :param actions: Actions to inline
        :return: None
        """
        if not self.windfile:
            return
        logger.info(
            "🌍",
            f"adding {len(actions)} actions",
            self.output_settings.emoji,
        )

        external_actions: typing.List[Action] = actions[1]
        types: typing.List[str] = actions[0]

        for index in range(len(external_actions)):
            new_name: str = f"{name}_{index}"

            self.metadata.append(
                scope="actions",
                key=new_name,
                subkey="original_type",
                value=types[index],
            )
            
            merge_environment(self.windfile.jobs[name].root.environment, external_actions[index])
            merge_parameters(
                self.windfile.jobs[name].root.parameters,
                external_actions[index],
            )
            merge_lifecycle(
                self.windfile.jobs[name].root.excludeDuring,
                external_actions[index],
            )
            logger.info("➕", f"adding action {external_actions[index]}", self.output_settings.emoji)
            self.metadata.append(
                scope="actions",
                key=new_name,
                subkey="original_name",
                value=name,
            )
            
            self.windfile.jobs[new_name] = external_actions[index]
        self.windfile.jobs.pop(name)

    def convert_external_action_to_internal(
        self,
        external_file: str,
        action: ExternalAction | FileAction | PlatformAction | Action,
    ) -> Optional[typing.Tuple[typing.List[str], typing.List[Action]]]:
        absolute_path: str = get_path_to_file(
            absolute_path=self.pwd(), relative_path=external_file
        )
        if not file_exists(
            path=absolute_path, output_settings=self.output_settings
        ):
            return None
        logger.debug(
            "✍️ ",
            f"rewriting {os.path.normpath(external_file)} to {absolute_path}",
            self.output_settings.emoji,
        )
        with open(absolute_path, encoding="utf-8") as file:
            if isinstance(action, FileAction):
                internal_action: Action = Action(
                    root=InternalAction(
                        script=file.read(),
                        excludeDuring=action.excludeDuring,
                        environment=action.environment,
                        parameters=action.parameters,
                        platform=action.platform,
                    )
                )
                return ["file"], [internal_action]

            if isinstance(action, ExternalAction):
                original_types: List[str] = []
                actions: typing.List[Action] = []
                logger.info(
                    "📄 ",
                    f"reading external action {absolute_path}",
                    self.output_settings.emoji,
                )
                external: Optional[ActionFile] = read_action_file(
                    file=file, output_settings=self.output_settings
                )
                if not external:
                    return None
                for name in external.steps:
                    internals: Step = external.steps[name]
                    internal: Optional[Action] = None
                    content: Optional[str] = None
                    if isinstance(internals.root, ExternalAction):
                        logger.error(
                            "❌",
                            "external actions in an external action are not supported yet",
                            self.output_settings.emoji,
                        )
                        return None
                    if isinstance(internals.root, InternalAction):
                        content = internals.root.script
                        original_types.append("internal")
                        internal = Action(
                            root=InternalAction(
                                script=internals.root.script,
                                excludeDuring=internals.root.excludeDuring,
                                environment=internals.root.environment,
                                parameters=internals.root.parameters,
                                platform=internals.root.platform,
                            )
                        )

                    elif isinstance(internals.root, PlatformAction):
                        original_types.append("platform")
                        content = get_content_of(
                            file=os.path.join(
                                os.path.dirname(absolute_path),
                                internals.root.file,
                            )
                        )
                        if not content:
                            logger.error(
                                "❌",
                                f"could not read file {internals.root.file}",
                                self.output_settings.emoji,
                            )
                            return None
                    elif isinstance(internals.root, FileAction):
                        original_types.append("file")
                        content = get_content_of(
                            file=get_path_to_file(
                                os.path.dirname(absolute_path),
                                internals.root.file,
                            )
                        )
                    else:
                        logger.error(
                            "❌",
                            f"unsupported action type {type(internals.root)}",
                            self.output_settings.emoji,
                        )
                        return None
                    if not content:
                        logger.error(
                            "❌",
                            f"could not read script of {name}",
                            self.output_settings.emoji,
                        )
                        return None
                    internal = Action(
                        root=InternalAction(
                            script=content,
                            excludeDuring=internals.root.excludeDuring,
                            environment=internals.root.environment,
                            parameters=internals.root.parameters,
                            platform=internals.root.platform,
                        )
                    )
                    if internal:
                        actions.append(internal)
                return original_types, actions
        return None

    def pwd(self) -> str:
        """
        Returns the current working directory of the windfile.
        :return: Current working directory of the windfile
        """
        return os.path.dirname(os.path.abspath(self.input_settings.file_path))

    def merge(self) -> Optional[WindFile]:
        """
        Merges the given windfile by inlining the external actions. So that the windfile can be
        used without other dependencies.
        :return: Merged windfile or none if the windfile could not be merged
        """

        if not self.merge_file_actions():
            return None
        if not self.merge_external_actions():
            return None
        if not self.merge_platform_actions():
            return None
        if not self.windfile:
            logger.error(
                "❌", "Merging failed. Aborting.", self.output_settings.emoji
            )
            return None
        if self.output_settings.verbose:
            # work-around as enums do not get cleanly printed with model_dump
            json: str = self.windfile.model_dump_json(exclude_none=True)
            logger.info("🪄", "Merged windfile", self.output_settings.emoji)
            print(yaml.dump(yaml.safe_load(json), sort_keys=False))
        return self.windfile
