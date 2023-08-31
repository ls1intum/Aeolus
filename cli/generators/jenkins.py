from typing import List, Optional

from classes.generated.definitions import InternalAction, Action, Target
from generators.base import BaseGenerator
from utils import logger


class JenkinsGenerator(BaseGenerator):
    """
    Jenkins generator. Generates a jenkins pipeline to be used in the Jenkins CI system.
    """

    def add_prefix(self) -> None:
        self.result.append("pipeline {")
        self.result.append("  agent any")
        if self.windfile.environment:
            self.result.append("  environment {")
            for env_var in self.windfile.environment.root.root:
                self.result.append(
                    f'    {env_var} = "{self.windfile.environment.root.root[env_var]}"'
                )
            self.result.append("  }")

        self.result.append("  stages {")
        self.result.append("    stage('Checkout code') {")
        self.result.append("      steps {")
        self.result.append("        checkout scm")
        self.result.append("      }")
        self.result.append("    }")

    def add_postfix(self) -> None:
        """
        Add the postfix to the pipeline
        """
        self.result.append("  }")
        self.result.append("}")

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
            if step.platform == Target.jenkins.name:
                logger.info(
                    "🔨",
                    "Platform action detected. Should be executed now...",
                    self.output_settings.emoji,
                )
                # TODO implement
                return None
            else:
                logger.info(
                    "🔨",
                    "Unfitting platform action detected. Skipping...",
                    self.output_settings.emoji,
                )
                return None
        self.result.append(f"    # step {name}")
        self.result.append(f"    # generated from step {original_name}")
        self.result.append(f"    # original type was {original_type}")
        self.result.append(f"    stage('{name}') " + "{")
        self.result.append(f"      steps " + "{")

        for line in step.script.split("\n"):
            if line:
                self.result.append(f"         {line}")
        self.result.append("      }")
        self.result.append("    }")
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
