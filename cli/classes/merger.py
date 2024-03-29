"""
Merger class. Merges external actions into the windfile to simplify the generation process.
"""
import os
import tempfile
import traceback
import typing
from typing import List, Optional
import yaml
from git import Repo

from classes.generated.actionfile import ActionFile
from classes.generated.definitions import (
    Parameters,
    Action,
    Dictionary,
    Lifecycle,
    Environment,
    PlatformAction,
    FileAction,
    TemplateAction,
    ScriptAction,
    Docker,
)
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.pass_metadata import PassMetadata
from classes.output_settings import OutputSettings
from classes.pass_settings import PassSettings
from classes.validator import (
    read_action_file,
    get_platform_actions,
    get_template_actions,
    get_file_actions,
    Validator,
    get_script_actions_with_names,
)
from cli_utils import logger, utils
from cli_utils.utils import get_content_of, get_path_to_file, file_exists


def merge_parameters(parameters: Parameters | None, action: Action) -> None:
    """
    Merges the given parameters into the parameters of the action.
    :param parameters: Parameters to merge into the action
    :param action: Action to merge the parameters into
    """
    if parameters:
        param_list: dict = action.root.parameters.root.root if action.root.parameters else {}
        param_list.update(parameters.root.root)
        action.root.parameters = Parameters(root=Dictionary(root=param_list))


def merge_environment(environment: Environment | None, action: Action) -> None:
    """
    Merges the given environment variables into the
    environment variables of the action.
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
    Creates a superset of the given lifecycle items and
    the lifecycle of the action and adds it to the action.
    :param lifecycle: lifecycle items to add
    :param action: action to add the lifecycle items to
    """
    if lifecycle:
        lifecycle_list: list = action.root.excludeDuring if action.root.excludeDuring else []
        lifecycle_list.extend(lifecycle)
        action.root.excludeDuring = list(set(lifecycle_list))


def merge_docker(docker: Docker | None, action: Action) -> None:
    """
    Merges the given docker configuration into the
    docker configuration of the action.
    :param docker: docker configuration to merge
    :param action: action to merge the docker configuration into
    """
    if docker:
        if ":" in docker.image:
            image: str = docker.image.split(":")[0]
            tag: str = docker.image.split(":")[1]
            docker.image = image
            docker.tag = tag
    if docker and action.root.docker is None:
        action.root.docker = docker


class Merger(PassSettings):
    """
    Merger class. Merges external actions into the
     windfile to simplify the generation process.
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

    def merge_script_actions(self) -> bool:
        """
        Merges the script actions into the windfile.
        Mainly sets metadata needed for the generation process.
        :return: True if the internal actions could be merged, False otherwise
        """
        if self.windfile is None:
            return False
        logger.info("🏠 ", "Merging script actions", self.output_settings.emoji)
        actions: List[tuple[str, Action]] = get_script_actions_with_names(self.windfile)
        for action in actions:
            index: int = [i for i, item in enumerate(self.windfile.actions) if action[0] == item.root.name][0]
            merge_docker(self.windfile.metadata.docker, self.windfile.actions[index])
        self.set_original_types(names=[action_tuple[0] for action_tuple in actions], key="script")
        self.set_original_names(names=[action_tuple[0] for action_tuple in actions])
        return True

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
        self.set_original_types(names=[action_tuple[0] for action_tuple in actions], key="file")
        return self.traverse_external_actions(external_actions=actions)

    def merge_template_actions(self) -> bool:
        """
        Merges the external actions into the windfile.
        :return: True if the external actions could be merged, False otherwise
        """
        logger.info("🌍", "Merging external actions", self.output_settings.emoji)
        actions: list[tuple[str, Action]] = get_template_actions(self.windfile)
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

    def pull_external_action(
        self, action: TemplateAction
    ) -> Optional[typing.Tuple[typing.List[str], typing.List[Action]]]:
        """
        Pulls the given external action from GitHub/or other GIT hostings and converts it to internal actions.
        :param action: External action to pull
        :return: Tuple of the original types and the converted actions
        """
        if not action.use:
            logger.error("❌ ", f"{action.use} not found", self.output_settings.emoji)
            return None
        slug: str = action.use
        if "/" not in slug:
            # we default to the ls1intum organization on GitHub
            slug = f"https://github.com/ls1intum/{slug}.git"
        if not slug.endswith(".git"):
            logger.error("❌ ", f"{slug} is not a git repository", self.output_settings.emoji)
            return None
        logger.info("📄 ", f"pulling {slug}", self.output_settings.emoji)
        with tempfile.TemporaryDirectory() as tmp:
            repo: Repo = Repo.clone_from(url=slug, to_path=tmp)
            if not repo:
                logger.error("❌ ", f"{slug} could not be cloned, make sure it is public", self.output_settings.emoji)
                return None
            default_name: str = "action.yaml"
            if not os.path.exists(os.path.join(tmp, default_name)):
                logger.error("❌ ", f"{slug} does not contain an action.yaml", self.output_settings.emoji)
                return None
            actionfile: Optional[ActionFile] = self.read_external_action_file(path=os.path.join(tmp, default_name))
            if not actionfile:
                logger.error("❌ ", f"{slug} does not contain an action.yaml", self.output_settings.emoji)
                return None
            return self.convert_actionfile_to_script_actions(actionfile=actionfile, absolute_path=tmp)

    def set_original_names(self, names: List[str]) -> None:
        """
        Sets the original name of the given actions to the given key.
        :param names: Names of the actions
        :param key: Key to set the original name to
        :return: None
        """
        for name in names:
            self.metadata.append(
                scope="actions",
                key=name,
                subkey="original_name",
                value=name,
            )

    def merge_platform_actions(self) -> bool:
        """
        Merges the platform actions into the windfile.
        :return: True if the platform actions could be merged, False otherwise
        """
        logger.info("🚉", "Merging platform actions", self.output_settings.emoji)
        actions: list[tuple[str, Action]] = get_platform_actions(self.windfile)
        logger.info(
            "🚉",
            f"found {len(actions)} platform actions",
            self.output_settings.emoji,
        )
        self.set_original_types(names=[action_tuple[0] for action_tuple in actions], key="platform")
        return self.traverse_external_actions(external_actions=actions)

    def read_external_action_file(self, path: str) -> Optional[ActionFile]:
        """
        Reads the given file and returns an ActionFile object.
        :param path: Path to the file to read
        :return: ActionFile object or None if the file could not be read
        """
        if not os.path.exists(path):
            logger.error("❌ ", f"{path} does not exist", self.output_settings.emoji)
            return None
        with open(path, encoding="utf-8") as file:
            return read_action_file(file=file, output_settings=self.output_settings)

    def traverse_external_actions(
        self,
        external_actions: List[typing.Tuple[str, Action]],
    ) -> bool:
        """
        Traverses the given list of external actions and inlines them into the windfile.
        :param external_actions: list of external actions
        :return: True if the external actions could be traversed, False otherwise
        """
        if not self.windfile:
            logger.error(
                "❌ ",
                "No windfile found. Aborting.",
                self.output_settings.emoji,
            )
            return False
        for name, action in external_actions:
            try:
                path: Optional[str] = None
                converted: Optional[
                    typing.Tuple[
                        typing.List[str],
                        typing.List[Action],
                    ]
                ] = None
                if isinstance(action, FileAction):
                    path = action.file
                elif isinstance(action, PlatformAction):
                    path = action.code
                    if path is None:
                        converted = ([name], [Action(root=action)])
                elif isinstance(action, TemplateAction):
                    path = action.use
                if path:
                    converted = self.convert_external_action_to_internal(
                        external_file=path,
                        action=action,
                    )
                    if not converted and isinstance(action, TemplateAction):
                        # try to pull the action from GitHub
                        converted = self.pull_external_action(action=action)
                    if not converted:
                        logger.error(
                            "❌ ",
                            f"{path} could not be converted",
                            self.output_settings.emoji,
                        )
                        return False
                    logger.info("📄 ", f"{path} converted", self.output_settings.emoji)

                if converted:
                    self.inline_actions(name=name, actions=converted)
            # ignore pylint: disable=broad-except
            except Exception as exception:
                logger.error("❌", f"{exception}", self.output_settings.emoji)
                if self.output_settings.debug:
                    traceback.print_exc()
                return False
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
            return None
        logger.info(
            "🌍",
            f"adding {len(actions)} actions",
            self.output_settings.emoji,
        )

        external_actions: typing.List[Action] = actions[1]
        types: typing.List[str] = actions[0]

        original_index: int = [i for i, item in enumerate(self.windfile.actions) if name == item.root.name][0]
        for index, action in enumerate(external_actions):
            new_name: str = f"{name}_{index}"

            self.metadata.append(
                scope="actions",
                key=new_name,
                subkey="original_type",
                value=types[index],
            )

            merge_environment(
                self.windfile.actions[original_index].root.environment,
                action,
            )
            merge_parameters(
                self.windfile.actions[original_index].root.parameters,
                action,
            )
            merge_lifecycle(
                self.windfile.actions[original_index].root.excludeDuring,
                action,
            )
            merge_docker(self.windfile.metadata.docker, action)
            logger.info(
                "➕",
                f"adding action {action}",
                self.output_settings.emoji,
            )
            self.metadata.append(
                scope="actions",
                key=new_name,
                subkey="original_name",
                value=name,
            )

            action.root.name = new_name
            self.windfile.actions.insert(original_index + index + 1, action)
        self.windfile.actions.pop(original_index)
        return None

    def convert_actionfile_to_script_actions(
        self, actionfile: ActionFile, absolute_path: str
    ) -> Optional[typing.Tuple[typing.List[str], typing.List[Action]]]:
        """
        Converts the given actionfile to script actions. By inlining the defined actions into the windfile.
        Platform actions need to stay platform actions.
        :param actionfile: Actionfile to convert
        :param absolute_path: Absolute path to the actionfile
        :return: Tuple of the original types and the converted actions
        """
        original_types: List[str] = []
        actions: List[Action] = []
        if actionfile is not None:
            for internals in actionfile.steps:
                internal: Optional[Action] = None
                content: Optional[str] = None
                if isinstance(internals.root, TemplateAction):
                    logger.error(
                        "❌ ",
                        "external actions in an external action are not supported yet",
                        self.output_settings.emoji,
                    )
                    return None
                if isinstance(internals.root, ScriptAction):
                    content = internals.root.script
                    original_types.append("internal")
                    internal = Action(
                        root=ScriptAction(
                            name=internals.root.name,
                            script=internals.root.script,
                            workdir=internals.root.workdir,
                            excludeDuring=internals.root.excludeDuring,
                            environment=internals.root.environment,
                            parameters=internals.root.parameters,
                            results=internals.root.results,
                            platform=internals.root.platform,
                            docker=internals.root.docker,
                            runAlways=internals.root.runAlways,
                        )
                    )

                elif isinstance(internals.root, PlatformAction):
                    original_types.append("platform")
                    if internals.root.code:
                        content = get_content_of(
                            file=os.path.join(
                                os.path.dirname(absolute_path),
                                internals.root.code,
                            )
                        )
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
                    content = None
                if not content and not isinstance(internals.root, PlatformAction):
                    logger.error(
                        "❌",
                        f"could not get content of {internals.root.name}",
                        self.output_settings.emoji,
                    )
                    return None
                if isinstance(internals.root, PlatformAction):
                    internal = Action(root=internals.root)
                elif content:
                    internal = Action(
                        root=ScriptAction(
                            name=internals.root.name,
                            script=content,
                            workdir=internals.root.workdir,
                            excludeDuring=internals.root.excludeDuring,
                            environment=internals.root.environment,
                            parameters=internals.root.parameters,
                            results=internals.root.results,
                            platform=internals.root.platform,
                            docker=internals.root.docker,
                            runAlways=internals.root.runAlways,
                        )
                    )
                if internal:
                    actions.append(internal)
        return original_types, actions

    def convert_external_action_to_internal(
        self,
        external_file: str,
        action: TemplateAction | FileAction | PlatformAction | Action,
    ) -> Optional[typing.Tuple[typing.List[str], typing.List[Action]]]:
        """
        Converts the given external action to an internal action. For
        easier management and code generation.
        :param external_file: Path to the external file
        :param action: Action to convert
        :return: Tuple of the original types and the converted actions
        """
        absolute_path: str = get_path_to_file(absolute_path=self.pwd(), relative_path=external_file)
        if not file_exists(path=absolute_path, output_settings=self.output_settings):
            return None
        logger.debug(
            "✍️ ",
            f"rewriting {os.path.normpath(external_file)} to {absolute_path}",
            self.output_settings.emoji,
        )

        with open(absolute_path, encoding="utf-8") as file:
            original_types: List[str] = []
            actions: typing.List[Action] = []
            if isinstance(action, FileAction):
                original_types.append("file")
                actions.append(
                    Action(
                        root=ScriptAction(
                            name=action.name,
                            script=file.read(),
                            workdir=action.workdir,
                            excludeDuring=action.excludeDuring,
                            environment=action.environment,
                            parameters=action.parameters,
                            results=action.results,
                            platform=action.platform,
                            docker=action.docker,
                            runAlways=action.runAlways,
                        )
                    )
                )
            if isinstance(action, PlatformAction):
                parameters: Parameters | None = action.parameters
                if not parameters:
                    parameters = Parameters(root=Dictionary(root={}))
                parameters.root.root["__aeolus_call_function"] = action.function
                original_types.append("platform")
                actions.append(
                    Action(
                        root=ScriptAction(
                            name=action.name,
                            script=file.read(),
                            workdir=action.workdir,
                            excludeDuring=action.excludeDuring,
                            environment=action.environment,
                            parameters=parameters,
                            results=action.results,
                            platform=action.platform,
                            docker=action.docker,
                            runAlways=action.runAlways,
                        )
                    )
                )
            if isinstance(action, TemplateAction):
                logger.info(
                    "📄 ",
                    f"reading external action {absolute_path}",
                    self.output_settings.emoji,
                )
                actionfile: Optional[ActionFile] = read_action_file(file=file, output_settings=self.output_settings)
                if actionfile:
                    external_converted: Optional[
                        typing.Tuple[
                            typing.List[str],
                            typing.List[Action],
                        ]
                    ] = self.convert_actionfile_to_script_actions(
                        actionfile=actionfile,
                        absolute_path=absolute_path,
                    )

                if external_converted:
                    original_types.extend(external_converted[0])
                    actions.extend(external_converted[1])
                else:
                    return None
            return original_types, actions

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
        if not self.windfile:
            validator: Validator = Validator(output_settings=self.output_settings, input_settings=self.input_settings)
            validated: Optional[WindFile] = validator.validate_wind_file()
            if validated:
                self.windfile = validated
        if (
            not self.merge_script_actions()
            or not self.merge_file_actions()
            or not self.merge_template_actions()
            or not self.merge_platform_actions()
        ):
            return None
        if not self.windfile:
            logger.error("❌", "Merging failed. Aborting.", self.output_settings.emoji)
            return None
        utils.clean_up(windfile=self.windfile, output_settings=self.output_settings)
        if self.output_settings.verbose:
            # work-around as enums do not get cleanly printed with model_dump
            json: str = self.windfile.model_dump_json(exclude_none=True)
            logger.info("🪄", "Merged windfile", self.output_settings.emoji)
            print(yaml.dump(yaml.safe_load(json), sort_keys=False))
        return self.windfile
