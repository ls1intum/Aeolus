# pylint: disable=duplicate-code
"""
Jenkins generator. Generates a jenkins pipeline to be used in the Jenkins CI system.
The generated pipeline is a scripted pipeline.
"""
from typing import Optional, List, Any
from xml.dom.minidom import Document, parseString, Element

import jenkins  # type: ignore

from classes.generated.definitions import ScriptAction, Target, Repository, Docker
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.pass_metadata import PassMetadata
from cli_utils import logger, utils
from generators.base import BaseGenerator


class JenkinsGenerator(BaseGenerator):
    """
    Jenkins generator. Generates a jenkins pipeline
    to be used in the Jenkins CI system.
    """

    def __init__(
        self, windfile: WindFile, input_settings: InputSettings, output_settings: OutputSettings, metadata: PassMetadata
    ):
        input_settings.target = Target.jenkins
        super().__init__(windfile, input_settings, output_settings, metadata)

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
        indentation: int = 0
        self.add_line(indentation=indentation, line="pipeline {")
        indentation += 2
        if self.windfile.metadata.docker is None:
            self.add_line(indentation=indentation, line="agent any")
        else:
            self.add_docker_config(config=self.windfile.metadata.docker, indentation=indentation + 2)
        # to respect the exclusion during different parts of the lifecycle
        # we need a parameter that holds the current lifecycle
        self.add_line(indentation=indentation, line="parameters {")
        # we set it to working_time by default, as this is the most common case, and we want to avoid
        # that the job does not execute stages only meant to be executed during evaluation (e.g. hidden tests)
        indentation += 2
        self.add_line(
            indentation=indentation,
            line="string(name: 'current_lifecycle', defaultValue: 'working_time', description: 'The current stage')",
        )
        indentation -= 2
        self.add_line(indentation=indentation, line="}")
        # to work with jenkins and bamboo, we need a way to access the repository url, as this is not possible
        # in a scripted jenkins pipeline, we set it as an environment variable
        self.add_repository_urls_to_environment()
        if self.windfile.environment:
            self.add_line(indentation=indentation, line="environment {")
            indentation += 2
            for env_var in self.windfile.environment.root.root:
                self.add_line(
                    indentation=indentation, line=f"{env_var} = '{self.windfile.environment.root.root[env_var]}'"
                )
            indentation -= 2
            self.add_line(indentation=indentation, line="}")
        assert indentation == 2  # we need to be at the same level as in the beginning, otherwise something is wrong
        self.add_line(indentation=indentation, line="stages {")

    def add_postfix(self) -> None:
        """
        Add the postfix to the pipeline
        """
        self.result.append("}")

    def handle_always_step(self, name: str, step: ScriptAction, indentation: int = 4) -> None:
        """
        Translate a step into a CI post action.
        :param name: Name of the step to handle
        :param step: to translate
        :param indentation: indentation level
        :return: CI action
        """
        original_name: Optional[str] = self.metadata.get_original_name_of(name)
        original_type: Optional[str] = self.metadata.get_meta_for_action(name).get("original_type")

        self.add_line(indentation=indentation, line=f"// step {name}")
        self.add_line(indentation=indentation, line=f"// generated from step {original_name}")
        self.add_line(indentation=indentation, line=f"// original type was {original_type}")
        self.add_script(
            wrapper="always", name=name, original_type=original_type, script=step.script, indentation=indentation
        )
        self.add_line(indentation=indentation - 2, line="}")

    # pylint: disable=too-many-arguments
    def add_script(self, wrapper: str, name: str, original_type: Optional[str], script: str, indentation: int) -> None:
        """
        Add a script to the pipeline.
        :param wrapper: wrapper to use, e.g. steps, post, always etc.
        :param name: Name of the step to handle
        :param original_type: original type of the action
        :param script: Script to add
        :param indentation: indentation level
        """
        self.result.append(" " * indentation + f"{wrapper} " + "{")
        indentation += 2
        self.result.append(" " * indentation + f"echo '⚙️ executing {name}'")
        was_internal_or_file: bool = original_type in ("file", "script")
        if was_internal_or_file:
            self.result.append(" " * indentation + "sh '''")
        for line in script.split("\n"):
            if line:
                self.result.append(" " * indentation + f"{line}")
        if was_internal_or_file:
            self.result.append(" " * indentation + "'''")
        indentation -= 2
        self.result.append(" " * indentation + "}")

    def handle_step(self, name: str, step: ScriptAction, call: bool) -> None:
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
        self.add_script(wrapper="steps", name=name, original_type=original_type, script=step.script, indentation=6)
        self.result.append("    }")
        return None

    def add_environment_variables(self, step: ScriptAction) -> None:
        """
        Add environment variables and parameters to the step.
        :param step: Step to add environment variables to
        """
        if step.environment is not None or step.parameters is not None:
            self.add_line(indentation=6, line="environment {")
            if step.parameters is not None:
                for param in step.parameters.root.root:
                    self.add_line(indentation=8, line=f'{param} = "{step.parameters.root.root[param]}"')
            if step.environment is not None:
                for env_var in step.environment.root.root:
                    self.add_line(indentation=8, line=f'{env_var} = "{step.environment.root.root[env_var]}"')
            self.add_line(indentation=6, line="}")

    def handle_clone(self, name: str, repository: Repository, indentation: int) -> None:
        """
        Handles the clone step.
        :param name: Name of the repository to clone
        :param repository: Repository ot checkout
        :param indentation: indentation level
        """
        original_indentation: int = indentation
        self.add_line(indentation=indentation, line=f"stage('{name}') " + "{")
        indentation += 2
        self.add_line(indentation=indentation, line="steps {")
        indentation += 2
        self.add_line(indentation=indentation, line=f"echo '🖨️ cloning {name}'")
        if repository.path != ".":
            self.add_line(indentation=indentation, line=f"dir('{repository.path}') " + "{")
            indentation += 2
        self.add_line(indentation=indentation, line="checkout([$class: 'GitSCM',")
        indentation += 2
        self.add_line(indentation=indentation, line="branches: [[name: '" + repository.branch + "']],")
        self.add_line(indentation=indentation, line="doGenerateSubmoduleConfigurations: false,")
        self.add_line(indentation=indentation, line="extensions: [],")
        self.add_line(indentation=indentation, line="submoduleCfg: [],")
        self.add_line(indentation=indentation, line="userRemoteConfigs: [[")
        indentation += 2
        if self.windfile.metadata.gitCredentials and isinstance(self.windfile.metadata.gitCredentials, str):
            self.add_line(
                indentation=indentation, line="credentialsId: '" + self.windfile.metadata.gitCredentials + "',"
            )
        self.add_line(indentation=indentation, line=f"name: '{name}',")
        url: str = repository.url
        if self.metadata.get(scope="repositories", key=name, subkey="url") is not None:
            repository_metadata: dict[str, Any] = self.metadata.get(scope="repositories")
            if repository_metadata is not None and name in repository_metadata and "url" in repository_metadata[name]:
                cached_value: str = repository_metadata[name]["url"]
                url = "${" + cached_value + "}"
        self.add_line(indentation=indentation, line=f"url: '{url}'")
        indentation -= 2
        self.add_line(indentation=indentation, line="]]")
        indentation -= 2
        self.add_line(indentation=indentation, line="])")
        indentation -= 2
        self.add_line(indentation=indentation, line="}")
        if repository.path != ".":
            indentation -= 2
            self.add_line(indentation=indentation, line="}")
        indentation -= 2
        self.add_line(indentation=indentation, line="}")
        assert indentation == original_indentation

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
        utils.replace_environment_variables_in_windfile(environment=self.environment, windfile=self.windfile)
        self.add_prefix()
        if self.windfile.repositories:
            for name in self.windfile.repositories:
                repository: Repository = self.windfile.repositories[name]
                self.handle_clone(name=name, repository=repository, indentation=4)
        for step in self.windfile.actions:
            if isinstance(step.root, ScriptAction) and not step.root.runAlways:
                self.handle_step(name=step.root.name, step=step.root, call=True)
        self.add_line(indentation=2, line="}")
        if self.has_always_actions():
            self.add_line(indentation=2, line="post {")
            for post_step in self.windfile.actions:
                if isinstance(post_step.root, ScriptAction) and post_step.root.runAlways:
                    self.handle_always_step(name=post_step.root.name, step=post_step.root)
        self.add_postfix()
        if self.output_settings.ci_credentials is not None:
            self.publish()
        return super().generate()

    def check(self, content: str) -> bool:
        raise NotImplementedError("check_syntax() not implemented")
