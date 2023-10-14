# pylint: disable=duplicate-code
from typing import Optional, List
from xml.dom.minidom import Document, parseString, Element

import jenkins  # type: ignore
from classes.generated.definitions import InternalAction, Action, Target, Repository, Docker
from generators.base import BaseGenerator
from utils import logger


class JenkinsGenerator(BaseGenerator):
    """
    Jenkins generator. Generates a jenkins pipeline
    to be used in the Jenkins CI system.
    """

    def add_docker_config(self, config: Optional[Docker], indentation: int) -> None:
        """
        Add the docker configuration to the pipeline or stage
        :param config: Docker configuration to add
        :param indentation: indentation level
        """
        if config is None:
            return
        tag: str = config.tag if config.tag is not None else "latest"
        self.result.append(" " * indentation + "agent {")
        self.result.append(" " * indentation + "  docker {")
        self.result.append(" " * indentation + "    image '" + config.image + ":" + tag + "'")
        args: Optional[str] = None
        if config.volumes is not None:
            args = "-v " + ":".join(config.volumes)
        if config.parameters is not None:
            if args is None:
                args = ""
            args += " " + " ".join(config.parameters)
        if args is not None:
            self.result.append(" " * indentation + "    args '" + args + "'")
        self.result.append(" " * indentation + "  }")
        self.result.append(" " * indentation + "}")

    def add_prefix(self) -> None:
        """
        Add the prefix to the pipeline, e.g. the agent,
        the environment, etc.
        """
        self.result.append("pipeline {")
        if self.windfile.metadata.docker is None:
            self.result.append("  agent any")
        else:
            self.add_docker_config(config=self.windfile.metadata.docker, indentation=4)
        # to respect the exclusion during different parts of the lifecycle
        # we need a parameter that holds the current lifecycle
        self.result.append("  parameters {")
        # we set it to working_time by default, as this is the most common case, and we want to avoid
        # that the job does not execute stages only meant to be executed during evaluation (e.g. hidden tests)
        self.result.append(
            "    string(name: 'current_lifecycle', defaultValue: 'working_time', description: 'The current stage')"
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
        self.add_script(name=name, original_type=original_type, script=step.script, indentation=8)
        self.result.append("      }")
        self.result.append("    }")

    def add_script(self, name: str, original_type: Optional[str], script: str, indentation: int) -> None:
        """
        Add a script to the pipeline.
        :param original_type: original type of the action
        :param name: Name of the step to handle
        :param indentation: indentation level
        :param script: Script to add
        """
        self.result.append(" " * indentation + f"echo '⚙️ executing {name}'")
        was_internal_or_file: bool = original_type in ("file", "internal")
        if was_internal_or_file:
            self.result.append(" " * indentation + "sh '''")
        for line in script.split("\n"):
            if line:
                self.result.append(" " * indentation + f"{line}")
        if was_internal_or_file:
            self.result.append(" " * indentation + "'''")

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
        self.add_docker_config(config=step.docker, indentation=6)

        if step.excludeDuring is not None:
            self.result.append("      when {")
            self.result.append("        anyOf {")
            for exclusion in step.excludeDuring:
                self.result.append(f"          expression {{ params.current_lifecycle != '{exclusion.name}' }}")
            self.result.append("        }")
            self.result.append("      }")
        self.add_environment_variables(step=step)
        self.result.append("      steps " + "{")
        self.add_script(name=name, original_type=original_type, script=step.script, indentation=8)
        # self.result.append(f"        echo '⚙️ executing {name}'")
        # for now, we assume that all file actions are shell scripts
        # if original_type in ("file", "internal"):
        #     self.result.append("        sh '''")
        # for line in step.script.split("\n"):
        #     if line:
        #         self.result.append(f"         {line}")
        # if original_type in ("file", "internal"):
        #     self.result.append("        '''")
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
        :param name: Name of the repository to clone
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
            self.result.append(f"{prefix}           credentialsId: '{self.windfile.metadata.gitCredentials}',")
        self.result.append(f"{prefix}           name: '{name}',")
        self.result.append(f"{prefix}           url: '{repository.url}'")
        self.result.append(f"{prefix}          ]]")
        self.result.append(f"{prefix}        ])")
        self.result.append(f"{prefix}      }}")
        if repository.path != ".":
            self.result.append(f"{prefix}    }}")
        self.result.append("    }")

    def run(self, job_id: str) -> None:
        """
        Run the pipeline in the Jenkins CI system.
        :param job_id: ID of the job to run
        :return: None
        """
        if self.output_settings.ci_credentials is None:
            raise ValueError("Publishing requires a CI URL and a token, with Jenkins we also need a username")
        server = jenkins.Jenkins(
            self.output_settings.ci_credentials.url,
            username=self.output_settings.ci_credentials.username,
            password=self.output_settings.ci_credentials.token,
        )
        job_name: str = job_id.replace("-", "/")
        logger.info("🔨", f"Triggering Jenkins build for {job_name}", self.output_settings.emoji)
        if self.output_settings.run_settings is not None:
            server.build_job(job_name, parameters={"current_lifecycle": self.output_settings.run_settings.stage})

    def publish(self) -> None:
        """
        Publish the pipeline to the Jenkins CI system.
        """
        if self.windfile.metadata.id is None:
            raise ValueError("Publishing requires an id")
        if self.output_settings.ci_credentials is None:
            raise ValueError("Publishing requires a CI URL and a token, with Jenkins we also need a username")
        server = jenkins.Jenkins(
            self.output_settings.ci_credentials.url,
            username=self.output_settings.ci_credentials.username,
            password=self.output_settings.ci_credentials.token,
        )

        pipeline_config: str = """
            <flow-definition plugin="workflow-job">
                <description/>
                <keepDependencies>false</keepDependencies>
                <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
                <script/>
                <sandbox>true</sandbox>
                </definition>
                <triggers/>
                <disabled>false</disabled>
            </flow-definition>
        """

        # Create the Jenkins Pipeline Job
        job_name: str = self.windfile.metadata.id.replace("-", "/")
        if "/" in job_name:
            path: List[str] = job_name.split("/")
            for i in range(len(path) - 1):
                server.create_folder(path[i], ignore_failures=True)
        exists: bool = server.job_exists(job_name)

        config_xml: Document = parseString(server.get_job_config(job_name) if exists else pipeline_config)

        script: Element = config_xml.getElementsByTagName("script")[0]
        if exists:
            script.removeChild(script.firstChild)
        script.appendChild(config_xml.createTextNode(super().generate()))

        server.upsert_job(job_name, config_xml.toxml())

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
            if isinstance(step.root, InternalAction) and not step.root.run_always:
                self.handle_step(name=name, step=step.root, call=True)
        self.result.append("  }")
        if self.has_always_actions():
            self.result.append("  post {")
            for name in self.windfile.actions:
                post_step: Action = self.windfile.actions[name]
                if isinstance(post_step.root, InternalAction) and post_step.root.run_always:
                    self.handle_always_step(name=name, step=post_step.root)
        self.add_postfix()
        if self.output_settings.ci_credentials is not None:
            self.publish()
        return super().generate()

    def check(self, content: str) -> bool:
        raise NotImplementedError("check_syntax() not implemented")
