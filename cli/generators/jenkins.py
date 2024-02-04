# pylint: disable=duplicate-code
"""
Jenkins generator. Generates a jenkins pipeline to be used in the Jenkins CI system.
The generated pipeline is a scripted pipeline.
"""
import os
import typing
from typing import Optional, List
from xml.dom.minidom import Document, parseString, Element

import jenkins  # type: ignore
from jinja2 import Environment, FileSystemLoader, Template

from classes.generated.definitions import Target, Action, ScriptAction
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

    template: Optional[Template] = None

    def __init__(
        self, windfile: WindFile, input_settings: InputSettings, output_settings: OutputSettings, metadata: PassMetadata
    ):
        input_settings.target = Target.jenkins
        super().__init__(windfile, input_settings, output_settings, metadata)

    def add_prefix(self) -> None:
        """
        Add the prefix to the pipeline, e.g. the agent,
        the environment, etc.
        """
        # to respect the exclusion during different parts of the lifecycle
        # we need a parameter that holds the current lifecycle
        # to work with jenkins and bamboo, we need a way to access the repository url, as this is not possible
        # in a scripted jenkins pipeline, we set it as an environment variable
        self.add_repository_urls_to_environment()

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
                <properties>
                <hudson.security.AuthorizationMatrixProperty>
                    <inheritanceStrategy class="org.jenkinsci.plugins.matrixauth.inheritance.InheritParentStrategy"/>
                </hudson.security.AuthorizationMatrixProperty>
                </properties>
            </flow-definition>
        """

        # Create the Jenkins Pipeline Job
        job_name: str = self.windfile.metadata.id
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
        self.key = job_name

    def generate_using_jinja2(self) -> str:
        """
        Generate the bash script to be used as a local CI system with jinja2.
        """
        if not self.template:
            env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "templates")))
            self.template = env.get_template("Jenkinsfile.j2")

        actions: List[Action] = []
        for action in self.windfile.actions:
            if action.root.platform and action.root.platform != Target.jenkins:
                continue
            if action.root.platform and action.root.platform == Target.jenkins:
                original_type: Optional[str] = self.metadata.get_meta_for_action(action.root.name).get("original_type")
                if original_type == "platform" and action.root.parameters:
                    logger.info(
                        "🔨",
                        "Platform action detected. Executing arbitrary code...",
                        self.output_settings.emoji,
                    )
                    try:
                        if (
                            isinstance(action.root, ScriptAction)
                            and action.root.script
                            and action.root.parameters.root
                            and action.root.parameters.root.root
                        ):
                            function: Optional[str] = str(action.root.parameters.root.root["__aeolus_call_function"])
                            code: Optional[str] = action.root.script
                            utils.execute_arbitrary_code(code=code, function=function, module_name=action.root.name)
                    except Exception as exception:  # pylint: disable=broad-except
                        logger.error(
                            "❌",
                            f"Error executing platform action: {exception}",
                            self.output_settings.emoji,
                        )
            actions.append(action)
            if action.root.results:
                for result in action.root.results:
                    self.add_result(action.root.workdir, result)

        data: dict[str, typing.Any] = {
            "docker": self.windfile.metadata.docker,
            "environment": self.windfile.environment.root.root if self.windfile.environment else None,
            "needs_lifecycle_parameter": self.needs_lifecycle_parameter,
            "repositories": self.windfile.repositories if self.windfile.repositories else None,
            "has_always_actions": self.has_always_actions(),
            "steps": [action.root for action in actions if not action.root.runAlways],
            "always_steps": [action.root for action in actions if action.root.runAlways],
            "metadata": self.windfile.metadata,
            "repo_metadata": self.metadata.get(scope="repositories"),
            "has_results": self.has_results(),
            "results": self.results,
        }

        # Render the template with your data
        rendered_script = self.template.render(data)

        return rendered_script

    def generate(self) -> str:
        """
        Generate the bash script to be used as a local CI system.
        :return: bash script
        """
        utils.replace_environment_variables_in_windfile(environment=self.environment, windfile=self.windfile)
        self.add_prefix()

        self.result = self.generate_using_jinja2()
        if self.output_settings.ci_credentials is not None:
            self.publish()
        return super().generate()

    def check(self, content: str) -> bool:
        raise NotImplementedError("check_syntax() not implemented")
