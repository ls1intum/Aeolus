import os
import traceback
import typing
from typing import Optional, Tuple, List

import argparse
import yaml

from classes.generated.actionfile import ActionFile, Step
from classes.generated.definitions import (
    FileAction,
    ExternalAction,
    Action,
    PlatformAction,
    InternalAction,
    Environment,
    Parameters,
    Dictionary,
    Lifecycle,
)
from classes.generated.windfile import WindFile
from commands.subcommand import Subcommand
from commands.validator import (
    Validator,
    get_file_actions,
    get_external_actions,
    read_action_file,
)


def merge_parameters(parameters: Parameters | None, action: Action) -> None:
    if parameters:
        param_list: dict = (
            action.root.parameters.root.root if action.root.parameters else {}
        )
        param_list.update(parameters.root.root)
        action.root.parameters = Parameters(root=Dictionary(root=param_list))


def merge_environment(environment: Environment | None, action: Action) -> None:
    if environment:
        env_list: dict = {}
        if action.root.environment:
            env_list = action.root.environment.root.root
        env_list.update(environment.root.root)
        action.root.environment = Environment(root=Dictionary(root=env_list))


def merge_lifecycle(lifecycle: List[Lifecycle] | None, action: Action) -> None:
    if lifecycle:
        lifecycle_list: list = (
            action.root.excludeDuring if action.root.excludeDuring else []
        )
        lifecycle_list.extend(lifecycle)
        action.root.excludeDuring = lifecycle_list


class Merger(Subcommand):
    windfile: Optional[WindFile] = None

    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--no-external",
            "-w",
            help="Do not inline external actions.",
            action="store_true",
        )
        # pylint: disable=duplicate-code
        parser.add_argument(
            "--input",
            "-i",
            help="Input file to read from",
            default="windfile.yaml",
            required=True,
            type=open,
        )

    def merge_file_actions(self) -> bool:
        if self.args.verbose:
            print("📄 Merging file actions")
        directory: str = os.path.dirname(os.path.abspath(self.args.input.name))
        actions: List[tuple[str, Action]] = get_file_actions(self.windfile)
        if self.args.verbose:
            print(f"📄 found {len(actions)} file actions")
        return self.traverse_external_actions(
            current_directory=directory, external_actions=actions
        )

    def merge_external_actions(self) -> bool:
        if self.args.verbose:
            print("🌍 Merging external actions")
        directory: str = os.path.dirname(os.path.abspath(self.args.input.name))
        actions: list[tuple[str, Action]] = get_external_actions(self.windfile)
        if self.args.verbose:
            print(f"🌍 found {len(actions)} external actions")
        return self.traverse_external_actions(
            current_directory=directory, external_actions=actions
        )

    def inline_external_actions(
        self, external_actions: List[Tuple[str, ExternalAction]]
    ) -> bool:
        if not self.windfile:
            if self.args.verbose:
                print("❌ No windfile found. Aborting.")
            return False
        for external_action_tuple in external_actions:
            external_action_name: str = external_action_tuple[0]
            external_action: ExternalAction = external_action_tuple[1]
            file: Optional[str] = external_action.use
            absolute_path: str = os.path.join(
                self.args.input.name, file if file else ""
            )
            action_file: Optional[ActionFile] = self.read_external_actionfile(
                path=absolute_path
            )
            if not action_file:
                continue
            for name in action_file.steps:
                internals: Step = action_file.steps[name]
                if not isinstance(internals.root, InternalAction):
                    print(
                        "❌ external actions in an "
                        "external action are not supported yet"
                    )
                    return False
                internal: Action = Action(
                    root=InternalAction(
                        script=internals.root.script,
                        excludeDuring=internals.root.excludeDuring,
                        environment=internals.root.environment,
                        parameters=internals.root.parameters,
                    )
                )
                self.windfile.jobs[f"{external_action_name}_{name}"] = internal
        return True

    def read_external_actionfile(self, path: str) -> Optional[ActionFile]:
        if not os.path.exists(path):
            if self.args.verbose:
                print(f"❌ {path} does not exist")
            return None
        with open(path, encoding="utf-8") as file:
            return read_action_file(path=file)

    def traverse_external_actions(
        self,
        current_directory: str,
        external_actions: List[Tuple[str, Action]],
    ) -> bool:
        if not self.windfile:
            if self.args.verbose:
                print("❌ No windfile found. Aborting.")
            return False
        for entry in external_actions:
            try:
                name: str = entry[0]
                action: Action = entry[1]
                path: Optional[str] = None
                if isinstance(action, FileAction):
                    path = action.file
                elif isinstance(action, ExternalAction):
                    path = action.use
                if not path:
                    print(f"❌ {path} could not be found")
                    return False
                converted: Optional[Action] | Optional[
                    typing.List[Action]
                ] = self.convert_external_action_to_internal(
                    windfile_directory=current_directory,
                    external_file=path,
                    action=action,
                )
                if not converted:
                    print(f"❌ {path} could not be converted")
                    return False
                if self.args.verbose:
                    print(f"📄 {path} converted")
                if not isinstance(converted, list):
                    # found no other way to do this
                    self.windfile.jobs[name] = converted  # type: ignore
                else:
                    self.inline_actions(name=name, actions=converted)
            # ignore pylint: disable=broad-except
            except Exception as exception:
                print(f"❌ {exception}")
                if self.args.debug:
                    traceback.print_exc()
        return True

    def inline_actions(self, name: str, actions: List[Action]) -> None:
        if not self.windfile:
            return
        if self.args.verbose:
            print(f"🌍adding {len(actions)} actions")
        for action in actions:
            merge_environment(
                self.windfile.jobs[name].root.environment, action
            )
            merge_parameters(
                self.windfile.jobs[name].root.parameters,
                action,
            )
            merge_lifecycle(
                self.windfile.jobs[name].root.excludeDuring,
                action,
            )
            if self.args.verbose:
                print(f"➕ adding action {action}")
            self.windfile.jobs[f"{name}_{actions.index(action)}"] = action
        self.windfile.jobs.pop(name)

    def convert_external_action_to_internal(
        self,
        windfile_directory: str,
        external_file: str,
        action: ExternalAction | FileAction | PlatformAction | Action,
    ) -> Optional[Action] | Optional[typing.List[Action]]:
        absolute_path: str = os.path.join(windfile_directory, external_file)
        if not os.path.exists(absolute_path):
            print(f"❌ {absolute_path} does not exist")
            return None
        if self.args.debug:
            print(
                f"✍️ rewriting {external_file} "
                f"to absolute path {absolute_path}"
            )
        with open(absolute_path, encoding="utf-8") as file:
            if isinstance(action, FileAction):
                internal_action: Action = Action(
                    root=InternalAction(
                        script=file.read(),
                        excludeDuring=action.excludeDuring,
                        environment=action.environment,
                        parameters=action.parameters,
                    )
                )
                return internal_action
            if isinstance(action, ExternalAction):
                actions: typing.List[Action] = []
                print(f"📄 reading external action {absolute_path}")
                external: Optional[ActionFile] = read_action_file(path=file)
                if not external:
                    return None
                for name in external.steps:
                    internals: Step = external.steps[name]
                    if not isinstance(internals.root, InternalAction):
                        print(
                            "❌ external actions in an external "
                            "action are not supported yet"
                        )
                        return None
                    internal: Action = Action(
                        root=InternalAction(
                            script=internals.root.script,
                            excludeDuring=internals.root.excludeDuring,
                            environment=internals.root.environment,
                            parameters=internals.root.parameters,
                        )
                    )
                    actions.append(internal)
                return actions
        return None

    def merge(self) -> bool:
        if self.args.debug:
            print("🔍setting mode to wind")
        self.args.wind = True
        validator: Validator = Validator(args=self.args)
        validated: WindFile | ActionFile | None = validator.validate()
        if isinstance(validated, WindFile):
            self.windfile = validated
        if not self.windfile:
            if self.args.verbose:
                print("❌ Validation failed. Aborting.")
            return False
        self.merge_file_actions()
        self.merge_external_actions()
        # work-around as enums do not get cleanly printed with model_dump
        json: str = self.windfile.model_dump_json(exclude_none=True)
        print(yaml.dump(yaml.safe_load(json), sort_keys=False))
        return True
