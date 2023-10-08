# pylint: disable=duplicate-code
from typing import Optional

from classes.generated.definitions import InternalAction, Action, Target, Repository
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
        self.result.append("}")

    def handle_always_step(self, name: str, step: InternalAction) -> None:
        """
        Translate a step into a CI post action.
        :param name: Name of the step to handle
        :param step: to translate
        :return: CI action
        """
        original_name: Optional[str] = self.metadata.get_original_name_of(name)
        original_type: Optional[str] = self.metadata.get_meta_for_action(name).get("original_type")

        self.result.append(f"    // step {name}")
        self.result.append(f"    // generated from step {original_name}")
        self.result.append(f"    // original type was {original_type}")
        self.result.append("      always " + "{")
        self.result.append(f"        echo '⚙️ executing {name}'")
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

    def handle_step(self, name: str, step: InternalAction, call: bool) -> None:
        """
        Translate a step into a CI action.
        :param name: Name of the step to handle
        :param step: to translate
        :param call: whether to call the step or not
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
        self.result.append(f"        echo '⚙️ executing {name}'")
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

    def handle_clone(self, name: str, repository: Repository) -> None:
        """
        Handles the clone step.
        :param name: Name of the repository
        :param repository: Repository ot checkout
        """
        prefix: str = ""
        self.result.append(f"    stage('{name}') {{")
        self.result.append(f"{prefix}      steps {{")
        self.result.append(f"{prefix}        echo '🖨️ cloning {name}'")
        if repository.path != ".":
            self.result.append(f"        dir('{repository.path}') {{")
            prefix = "  "
        self.result.append(f"{prefix}        checkout([$class: 'GitSCM',")
        self.result.append(f"{prefix}          branches: [[name: '{repository.branch}']],")
        self.result.append(f"{prefix}          doGenerateSubmoduleConfigurations: false,")
        self.result.append(f"{prefix}          extensions: [],")
        self.result.append(f"{prefix}          submoduleCfg: [],")
        self.result.append(f"{prefix}          userRemoteConfigs: [[")
        if self.windfile.metadata.gitCredentials:
            self.result.append(f"{prefix}             credentialsId: '{self.windfile.metadata.gitCredentials}',")
        self.result.append(f"{prefix}             name: '{name}',")
        self.result.append(f"{prefix}             url: '{repository.url}'")
        self.result.append(f"{prefix}          ]]")
        self.result.append(f"{prefix}        ])")
        self.result.append(f"{prefix}      }}")
        if repository.path != ".":
            self.result.append(f"{prefix}    }}")
        self.result.append("    }")

    def generate(self) -> str:
        """
        Generate the bash script to be used as a local CI system.
        :return: bash script
        """
        self.add_prefix()
        if self.windfile.repositories:
            for name in self.windfile.repositories:
                repository: Repository = self.windfile.repositories[name]
                self.handle_clone(name=name, repository=repository)
        for name in self.windfile.actions:
            step: Action = self.windfile.actions[name]
            if isinstance(step.root, InternalAction) and not step.root.always:
                self.handle_step(name=name, step=step.root, call=True)
        self.result.append("  }")
        if self.has_always_actions():
            self.result.append("  post {")
            for name in self.windfile.actions:
                step: Action = self.windfile.actions[name]
                if isinstance(step.root, InternalAction) and step.root.always:
                    self.handle_always_step(name=name, step=step.root)
        self.add_postfix()
        return super().generate()

    def check(self, content: str) -> bool:
        raise NotImplementedError("check_syntax() not implemented")
