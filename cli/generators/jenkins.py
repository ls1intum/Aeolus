# pylint: disable=duplicate-code
from typing import Optional

from classes.generated.definitions import InternalAction, Action, Target, ExternalAction
from generators.base import BaseGenerator
from utils import logger


class JenkinsGenerator(BaseGenerator):
    """
    Jenkins generator. Generates a jenkins pipeline
    to be used in the Jenkins CI system.
    """

    def add_prefix(self) -> None:
        """
        Add the prefix to the pipeline, e.g. the agent,
        the environment, etc.
        """
        self.result.append("pipeline {")
        self.result.append("  agent any")
        # to respect the exclusion during different parts of the lifecycle
        # we need a parameter that holds the current lifecycle
        self.result.append("  parameters {")
        # we set it to working_time by default, as this is the most common case and we want to avoid
        # that the job does not execute stages only meant to be executed during evaluation (e.g. hidden tests)
        self.result.append(
            "    string(name: 'current_lifecycle', defaultValue: 'working_time', description: 'The current lifecycle')"
        )
        self.result.append("  }")
        if self.windfile.environment:
            self.result.append("  environment {")
            for env_var in self.windfile.environment.root.root:
                self.result.append(f'    {env_var} = "' f'{self.windfile.environment.root.root[env_var]}"')
            self.result.append("  }")

        self.result.append("  stages {")

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
        original_type: Optional[str] = self.metadata.get_meta_for_action(name).get("original_type")
        if original_type == "platform":
            if step.platform == Target.jenkins.name:
                logger.info(
                    "🔨",
                    "Platform action detected. Should be executed now...",
                    self.output_settings.emoji,
                )
                # TODO implement # pylint: disable=fixme
                return None
            logger.info(
                "🔨",
                "Unfitting platform action detected. Skipping...",
                self.output_settings.emoji,
            )
            return None
        self.result.append(f"    // step {name}")
        self.result.append(f"    // generated from step {original_name}")
        self.result.append(f"    // original type was {original_type}")
        self.result.append(f"    stage('{name}') " + "{")
        if step.excludeDuring is not None:
            self.result.append("      when {")
            self.result.append("        anyOf {")
            for exclusion in step.excludeDuring:
                self.result.append(f"          expression {{ params.current_lifecycle != '{exclusion.name}' }}")
            self.result.append("        }")
            self.result.append("      }")
        self.add_environment_variables(step=step)
        self.result.append("      steps " + "{")

        # for now, we assume that all file actions are shell scripts
        if original_type in ("file", "internal"):
            self.result.append("        sh '''")
        for line in step.script.split("\n"):
            if line:
                self.result.append(f"         {line}")
        if original_type in ("file", "internal"):
            self.result.append("        '''")
        self.result.append("      }")
        self.result.append("    }")
        return None

    def add_environment_variables(self, step: InternalAction) -> None:
        """
        Add environment variables and parameters to the step.
        :param step: Step to add environment variables to
        """
        if step.environment is not None or step.parameters is not None:
            self.result.append("      environment {")
            if step.parameters is not None:
                for param in step.parameters.root.root:
                    self.result.append(f'        {param} = "{step.parameters.root.root[param]}"')
            if step.environment is not None:
                for env_var in step.environment.root.root:
                    self.result.append(f'        {env_var} = "' f'{step.environment.root.root[env_var]}"')
            self.result.append("      }")

    def handle_clone(self, name: str, step: ExternalAction) -> None:
        """
        Handles the clone step.
        :param name: Name of the step
        :param step: Step to handle
        """
        if step.parameters is None or step.parameters.root is None or step.parameters.root.root is None:
            logger.error(
                "🔨",
                f"Clone step {name} does not have any parameters. Skipping...",
                self.output_settings.emoji,
            )
            return None
        directory: str = str(step.parameters.root.root["path"]) if "path" in step.parameters.root.root else "."
        prefix: str = ""
        self.result.append(f"    stage('{name}') {{")
        self.result.append(f"{prefix}      steps {{")
        if directory != ".":
            self.result.append(f"        dir('{directory}') {{")
            prefix = "  "
        self.result.append(f"{prefix}        checkout([$class: 'GitSCM',")
        self.result.append(f"{prefix}          branches: [[name: '{step.parameters.root.root['branch']}']],")
        self.result.append(f"{prefix}          doGenerateSubmoduleConfigurations: false,")
        self.result.append(f"{prefix}          extensions: [],")
        self.result.append(f"{prefix}          submoduleCfg: [],")
        self.result.append(f"{prefix}          userRemoteConfigs: [[")
        if self.windfile.metadata.gitCredentials:
            self.result.append(f"{prefix}             credentialsId: '{self.windfile.metadata.gitCredentials}',")
        self.result.append(f"{prefix}             name: '{name}',")
        self.result.append(f"{prefix}             url: '{step.parameters.root.root['repository']}'")
        self.result.append(f"{prefix}          ]]")
        self.result.append(f"{prefix}        ])")
        self.result.append(f"{prefix}      }}")
        if directory != ".":
            self.result.append(f"{prefix}    }}")
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

    def check(self, content: str) -> bool:
        raise NotImplementedError("check_syntax() not implemented")
