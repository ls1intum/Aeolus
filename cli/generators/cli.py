from typing import List, Optional

from classes.generated.definitions import InternalAction, Action
from generators.base import BaseGenerator
from utils import logger


class CliGenerator(BaseGenerator):
    """
    CLI generator. Generates a bash script to be used as a local CI system.
    """

    functions: List[str] = []

    def add_prefix(self) -> None:
        """
        Add the prefix to the bash script. E.g. the shebang, some output settings, etc.
        """
        self.result.append("#!/usr/bin/env bash")
        self.result.append("set -e")
        if self.output_settings.debug:
            self.result.append("set -x")

    def add_postfix(self) -> None:
        """
        Add the postfix to the bash script. E.g. some output settings, the callable functions etc.
        """
        self.result.append("\n")
        for function in self.functions:
            self.result.append(f"echo '⚙️ executing {function}'")
            self.result.append(f"{function}")

    def handle_step(self, name: str, step: InternalAction) -> None:
        """
        Translate a step into a CI action.
        :param name: Name of the step to handle
        :param step: to translate
        :return: CI action
        """
        original_name: Optional[str] = self.metadata.get_original_name_of(name)
        original_type: Optional[str] = self.metadata.get_meta_for_action(
            name
        ).get("original_type")
        if original_type == "platform":
            logger.info(
                "🔨",
                "Platform action detected. Skipping...",
                self.output_settings.emoji,
            )
            return None
        self.result.append(f"# step {name}")
        self.result.append(f"# generated from step {original_name}")
        self.result.append(f"# original type was {original_type}")
        self.functions.append(name)
        self.result.append(f"{name} () " + "{")

        for line in step.script.split("\n"):
            if line:
                self.result.append(f"  {line}")
        self.result.append("}")
        return None

    def generate(self) -> str:
        """
        Generate the bash script to be used as a local CI system.
        :return: bash script
        """
        self.add_prefix()
        for name in self.windfile.jobs:
            step: Action = self.windfile.jobs[name]
            if isinstance(step.root, InternalAction):
                self.handle_step(name=name, step=step.root)

        self.add_postfix()
        return super().generate()
