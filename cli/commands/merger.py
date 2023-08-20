import os
import sys
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
    get_actions_of_type,
)


def merge_parameters(parameters: Parameters | None, action: Action):
    if parameters:
        parameter_list: dict = (
            action.root.parameters.root.root if action.root.parameters else {}
        )
        parameter_list.update(parameters.root.root)
        action.root.parameters = Parameters(root=Dictionary(root=parameter_list))


def merge_environment(environment: Environment | None, action: Action):
    if environment:
        environment_list: dict = (
            action.root.environment.root.root if action.root.environment else {}
        )
        environment_list.update(environment.root.root)
        action.root.environment = Environment(root=Dictionary(root=environment_list))


def merge_lifecycle(lifecycle: List[Lifecycle] | None, action: Action):
    if lifecycle:
        lifecycle_list: list = action.root.excludeDuring if action.root.excludeDuring else []
        lifecycle_list.extend(lifecycle)
        action.root.excludeDuring = lifecycle_list


class Merger(Subcommand):
    windfile: Optional[WindFile] = None

    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser):
        parser.add_argument(
            "--no-external",
            "-w",
            help="Do not inline external actions.",
            action="store_true",
        )
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
        windfile_directory: str = os.path.dirname(os.path.abspath(self.args.input.name))
        file_actions: List[tuple[str, Action]] = get_file_actions(self.windfile)
        if self.args.verbose:
            print(f"📄 found {len(file_actions)} file actions")
        return self.traverse_external_actions(
            current_directory=windfile_directory, external_actions=file_actions
        )

    def merge_external_actions(self) -> bool:
        if self.args.verbose:
            print("🌍 Merging external actions")
        windfile_directory: str = os.path.dirname(os.path.abspath(self.args.input.name))
        external_actions: list[tuple[str, Action]] = get_external_actions(self.windfile)
        if self.args.verbose:
            print(f"🌍 found {len(external_actions)} external actions")
        return self.traverse_external_actions(
            current_directory=windfile_directory, external_actions=external_actions
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
                        "❌ external actions in an external action are not supported yet"
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
        with open(path) as f:
            return read_action_file(path=f)

    def traverse_external_actions(
        self,
        current_directory: str,
        external_actions: List[Tuple[str, Action]],
    ) -> bool:
        if not self.windfile:
            if self.args.verbose:
                print("❌ No windfile found. Aborting.")
            return False
        for external_action_tuple in external_actions:
            try:
                external_action_name: str = external_action_tuple[0]
                external_action: Action = external_action_tuple[1]
                path: Optional[str] = None
                if isinstance(external_action, FileAction):
                    path = external_action.file
                elif isinstance(external_action, ExternalAction):
                    path = external_action.use
                if not path:
                    print(f"❌ {path} could not be found")
                    return False
                converted: Optional[Action] | Optional[
                    typing.List[Action]
                ] = self.convert_external_action_to_internal(
                    windfile_directory=current_directory,
                    external_file=path,
                    action=external_action,
                )
                if not converted:
                    print(f"❌ {path} could not be converted")
                    return False
                if self.args.verbose:
                    print(f"📄 {path} converted")
                if not isinstance(converted, list):
                    self.windfile.jobs[external_action_name] = converted  # type: ignore # found no other way to do this
                else:
                    if self.args.verbose:
                        print(f"🌍adding {len(converted)} actions")
                    for action in converted:
                        merge_environment(
                            self.windfile.jobs[external_action_name].root.environment,
                            action,
                        )
                        merge_parameters(
                            self.windfile.jobs[external_action_name].root.parameters,
                            action,
                        )
                        merge_lifecycle(
                            self.windfile.jobs[external_action_name].root.excludeDuring,
                            action,
                        )
                        if self.args.verbose:
                            print(f"➕ adding action {action}")
                        self.windfile.jobs[
                            f"{external_action_name}_{converted.index(action)}"
                        ] = action
                    self.windfile.jobs.pop(external_action_name)
            except Exception as e:
                print(f"❌ {e}")
        return True

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
            print(f"✍️ rewriting {external_file} to absolute path {absolute_path}")
        with open(absolute_path) as f:
            if isinstance(action, FileAction):
                internal_action: Action = Action(
                    root=InternalAction(
                        script=f.read(),
                        excludeDuring=action.excludeDuring,
                        environment=action.environment,
                        parameters=action.parameters,
                    )
                )
                return internal_action
            elif isinstance(action, ExternalAction):
                actions: typing.List[Action] = []
                print(f"📄 reading external action {absolute_path}")
                external_action: Optional[ActionFile] = read_action_file(path=f)
                if not external_action:
                    return None
                for name in external_action.steps:
                    internals: Step = external_action.steps[name]
                    if not isinstance(internals.root, InternalAction):
                        print(
                            "❌ external actions in an external action are not supported yet"
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
