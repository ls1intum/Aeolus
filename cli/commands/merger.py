import io
import os
import sys
import typing
from typing import Optional, Tuple, List

import argparse
import yaml

from classes.generated.action import ActionFile, InternalAction as ActionInternalAction
from classes.generated.windfile import (
    WindFile,
    InternalAction,
    FileAction,
    ExternalAction,
    PlatformAction,
    Action,
)
from commands.subcommand import Subcommand
from commands.validator import (
    Validator,
    get_file_actions,
    get_external_actions,
    read_action_file,
    has_external_actions,
)


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
        file_actions: List[Tuple[str, FileAction]] = get_file_actions(self.windfile)
        self.traverse_external_actions(
            current_directory=windfile_directory, external_actions=file_actions
        )
        return True

    def merge_external_actions(self) -> bool:
        if self.args.verbose:
            print("🌍 Merging external actions")
        windfile_directory: str = os.path.dirname(os.path.abspath(self.args.input.name))
        external_actions: List[Tuple[str, ExternalAction]] = get_external_actions(
            self.windfile
        )
        print(external_actions)
        self.traverse_external_actions(
            current_directory=windfile_directory, external_actions=external_actions
        )
        return True

    def traverse_external_actions(
        self,
        current_directory: str,
        external_actions: List[Tuple[str, ExternalAction | FileAction]],
    ) -> bool:
        for external_action_tuple in external_actions:
            try:
                external_action_name: str = external_action_tuple[0]
                external_action: ExternalAction | FileAction = external_action_tuple[1]
                path: Optional[str] = None
                if isinstance(external_action, FileAction):
                    path = external_action.file
                elif isinstance(external_action, ExternalAction):
                    path = external_action.use
                if not path:
                    continue
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
                print(f"📄 {path} converted")
                print(type(converted))
                if not isinstance(converted, list):
                    self.windfile.jobs[external_action_name] = converted  # type: ignore # found no other way to do this
                else:
                    print(f"📄 adding {len(converted)} actions")
                    for action in converted:
                        print(f"📄 adding action {action}")
                        self.windfile.jobs[
                            f"{external_action_name}_{converted.index(action)}"
                        ] = action
            except Exception as e:
                print(f"❌ {e}")
        return True

    def convert_external_action_to_internal(
        self,
        windfile_directory: str,
        external_file: str,
        action: ExternalAction | FileAction | PlatformAction,
    ) -> Optional[Action] | Optional[typing.List[Action]]:
        absolute_path: str = os.path.join(windfile_directory, external_file)
        if not os.path.exists(absolute_path):
            print(f"❌ {absolute_path} does not exist")
            return None
        if self.args.debug:
            print(f"✍️ rewriting {external_file} to absolute path {absolute_path}")
        with open(absolute_path) as f:
            internal: Optional[Action] = None
            if isinstance(action, FileAction):
                internal: Action = Action(
                    root=InternalAction(
                        script=f.read(),
                        exclude_during=action.exclude_during,
                        environment=action.environment,
                        parameters=action.parameters,
                    )
                )
                return internal
            if isinstance(action, ExternalAction):
                actions: typing.List[Action] = []
                print(f"📄 reading external action {absolute_path}")
                external_action: Optional[ActionFile] = read_action_file(path=f)
                if not external_action:
                    return None
                for name in external_action.steps:
                    internals: Action = external_action.steps[name]
                    if not isinstance(internals.root, ActionInternalAction):
                        print(
                            "❌ external actions in an external action are not supported yet"
                        )
                        return None
                    internal: Action = Action(
                        root=InternalAction(
                            script=internals.root.script,
                            exclude_during=internals.root.exclude_during,
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
        yaml.dump(self.windfile.model_dump(exclude_none=True), sys.stdout)
        return True
