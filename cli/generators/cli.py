# pylint: disable=duplicate-code
import subprocess
import tempfile
from typing import List, Optional

from classes.generated.definitions import InternalAction, Action, ExternalAction
from generators.base import BaseGenerator
from utils import logger


class CliGenerator(BaseGenerator):
    """
    CLI generator. Generates a bash script to be used as a local CI system.
    """

    functions: List[str] = []

    def add_prefix(self) -> None:
        """
        Add the prefix to the bash script.
        E.g. the shebang, some output settings, etc.
        """
        self.result.append("#!/usr/bin/env bash")
        self.result.append("set -e")
        # if self.output_settings.debug:
        #     self.result.append("set -x")
        if self.windfile.environment:
            for env_var in self.windfile.environment.root.root:
                self.result.append(f'export {env_var}="' f'{self.windfile.environment.root.root[env_var]}"')

    def add_postfix(self) -> None:
        """
        Add the postfix to the bash script.
        E.g. some output settings, the callable functions etc.
        """
        self.result.append("\n")
        self.result.append("# main function")
        self.result.append("main () " + "{")
        self.result.append('  local _current_lifecycle="${1}"')
        for function in self.functions:
            self.result.append(f"  {function} $_current_lifecycle")
        self.result.append("}\n")
        self.result.append("main $@")

    def handle_step(self, name: str, step: InternalAction) -> None:
        """
        Translate a step into a CI action.
        :param name: Name of the step to handle
        :param step: to translate
        :return: CI action
        """
        original_name: Optional[str] = self.metadata.get_original_name_of(name)
        original_type: Optional[str] = self.metadata.get_meta_for_action(name).get("original_type")
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
        if step.excludeDuring is not None:
            # we don't need the local variable if there are no exclusions
            self.result.append('  local _current_lifecycle="${1}"')

            for exclusion in step.excludeDuring:
                self.result.append(f'  if [[ "${{_current_lifecycle}}" == "{exclusion.name}" ]]; then')
                self.result.append(f"    echo '⚠️  {name} is excluded during {exclusion.name}'")
                self.result.append("    return 0")
                self.result.append("  fi")

        self.result.append(f"  echo '⚙️  executing {name}'")
        if step.environment:
            for env_var in step.environment.root.root:
                self.result.append(f'  export {env_var}="' f'{step.environment.root.root[env_var]}"')
        if step.parameters is not None:
            for parameter in step.parameters.root.root:
                self.result.append(f'  {parameter}="{step.parameters.root.root[parameter]}"')
        for line in step.script.split("\n"):
            if line:
                self.result.append(f"  {line}")
        self.result.append("}")
        return None

    def check(self, content: str) -> bool:
        """
        Check the generated bash file for syntax errors.
        """
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(content.encode())
            temp.flush()
            stderr: str
            stdout: str
            has_passed: bool = False
            try:
                child: subprocess.CompletedProcess = subprocess.run(
                    f"bash -n {temp.name}",
                    text=True,
                    shell=True,
                    capture_output=True,
                    check=True,
                )
                has_passed = child.returncode == 0
                stderr = child.stderr
                stdout = child.stdout
            except subprocess.CalledProcessError as exception:
                stderr = exception.stderr
                stdout = exception.stdout
            if not has_passed:
                if stderr:
                    logger.error("❌ st", stderr, self.output_settings.emoji)
                if stdout:
                    logger.error("❌ ", stdout, self.output_settings.emoji)
            return has_passed

    def handle_clone(self, name: str, step: ExternalAction) -> None:
        """
        Handles the clone step.
        :param name: Name of the step
        :param step: Clone step to handle
        """
        if step.parameters is None or step.parameters.root is None or step.parameters.root.root is None:
            logger.error(
                "🔨",
                f"Clone step {name} does not have any parameters. Skipping...",
                self.output_settings.emoji,
            )
            return None
        directory: str = str(step.parameters.root.root["path"]) if "path" in step.parameters.root.root else "."
        self.result.append(f"# step {name}")
        self.result.append(f"# generated from step {name}")
        self.result.append(f"# original type was {step.use}")
        self.result.append(f"{name} () " + "{")
        self.result.append(f"  echo '🖨️ cloning {name}'")
        self.result.append(f"  git clone {step.parameters.root.root['repository']} {directory}")
        self.result.append("}")
        self.functions.append(name)
        return None

    def generate(self) -> str:
        """
        Generate the bash script to be used as a local CI system.
        :return: bash script
        """
        self.add_prefix()
        for name in self.windfile.jobs:
            step: Action = self.windfile.jobs[name]
            if isinstance(step.root, ExternalAction):
                # This is a workaround to be able to clone repositories before we
                # have the ability to include them directly from actions defined
                # in repositories. So clone-default is a special action, for now.
                if step.root.use == "clone-default":
                    self.handle_clone(name=name, step=step.root)
            if isinstance(step.root, InternalAction):
                self.handle_step(name=name, step=step.root)

        self.add_postfix()
        return super().generate()
