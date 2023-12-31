# pylint: disable=duplicate-code
import os
import re
import subprocess
import tempfile
import typing
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, Template
from docker.client import DockerClient  # type: ignore
from docker.models.containers import Container  # type: ignore
from docker.types.daemon import CancellableStream  # type: ignore

from classes.generated.definitions import ScriptAction, Repository, Target
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.pass_metadata import PassMetadata
from cli_utils import logger, utils
from generators.base import BaseGenerator


class CliGenerator(BaseGenerator):
    """
    CLI generator. Generates a bash script to be used as a local CI system.
    """

    functions: List[str] = []

    initial_directory_variable: str = "AEOLUS_INITIAL_DIRECTORY"

    template: Optional[Template] = None

    def __init__(
        self, windfile: WindFile, input_settings: InputSettings, output_settings: OutputSettings, metadata: PassMetadata
    ):
        input_settings.target = Target.cli
        self.functions = []
        super().__init__(windfile, input_settings, output_settings, metadata)

    def handle_step(self, name: str, step: ScriptAction, call: bool) -> None:
        """
        Translate a step into a CI action.
        :param name: Name of the step to handle
        :param step: to translate
        :param call: whether to call the step or not
        :return: CI action
        """
        original_type: Optional[str] = self.metadata.get_meta_for_action(name).get("original_type")
        if original_type == "platform" or (step.platform and step.platform != Target.cli):
            logger.info(
                "🔨",
                "Platform action detected. Skipping...",
                self.output_settings.emoji,
            )
            return None
        valid_funtion_name: str = re.sub("[^a-zA-Z_]+", "", name)
        if valid_funtion_name in self.functions:
            logger.info(
                "💥",
                f"Function name {valid_funtion_name} already exists. Adding a number to it...",
                self.output_settings.emoji,
            )
            number: int = 1
            while f"{valid_funtion_name}_{number}" in self.functions:
                number += 1
            valid_funtion_name += f"_{number}"
        if call:
            self.functions.append(valid_funtion_name)
        step.name = valid_funtion_name

        if step.results:
            if self.windfile.metadata.moveResultsTo:
                self.before_results[step.name] = [result for result in step.results if result.before]
            if self.windfile.metadata.moveResultsTo:
                self.after_results[step.name] = [result for result in step.results if result.before]
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
                    logger.error("❌ ", stderr, self.output_settings.emoji)
                if stdout:
                    logger.error("❌ ", stdout, self.output_settings.emoji)
            return has_passed

    def determine_docker_image(self) -> str:
        """
        Determine the docker image to use.
        :return: docker image
        """
        container_image: str = os.getenv("AEOLUS_WORKER_IMAGE", "ghcr.io/ls1intum/aeolus/worker:nightly")
        if self.windfile.metadata.docker is not None:
            container_image = self.windfile.metadata.docker.image
            tag: str = "latest"
            if self.windfile.metadata.docker.tag is not None:
                tag = self.windfile.metadata.docker.tag
            if ":" not in container_image:
                container_image += ":" + tag
        return container_image

    def run(self, job_id: str) -> None:
        """
        Run the generated bash script.
        """
        if self.output_settings.run_settings is None:
            return
        if self.final_result is None:
            self.generate()
        if self.final_result is None:
            return
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(self.generate().encode())
            temp.flush()
            client: DockerClient = DockerClient.from_env()
            container_name: str = "aeolus-worker" if job_id is None else f"aeolus-worker-{job_id}"
            container_image: str = self.determine_docker_image()
            volumes: dict[str, dict[str, str]] = {temp.name: {"bind": "/entrypoint.sh", "mode": "ro"}}
            if self.windfile.repositories:
                for name in self.windfile.repositories:
                    repository: Repository = self.windfile.repositories[name]
                    if repository.path:
                        volumes[repository.path] = {"bind": f"/{repository.path}", "mode": "rw"}
            client.containers.run(
                image=container_image,
                command=f"bash /entrypoint.sh {self.output_settings.run_settings.stage}",
                volumes=volumes,
                auto_remove=False,
                name=container_name,
                detach=True,
            )
            container: Container = client.containers.get(container_name)
            logs: CancellableStream = container.logs(stream=True, stdout=True, stderr=True)
            lines: List[str] = logs.next().decode("utf-8").split("\n")
            while container.status == "running" or lines:
                try:
                    for line in lines:
                        if line:
                            print(line)
                    lines = logs.next().decode("utf-8").split("\n")
                except StopIteration:
                    break
            container.remove()
            os.unlink(temp.name)
        return

    def generate_using_jinja2(self) -> str:
        """
        Generate the bash script to be used as a local CI system with jinja2.
        """
        # Load the template from the file system
        if not self.template:
            env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "templates")))
            self.template = env.get_template("cli.sh.j2")

        # Prepare your data
        data: dict[str, typing.Any] = {
            "has_multiple_steps": self.has_multiple_steps,
            "initial_directory_variable": self.initial_directory_variable,
            "environment": self.windfile.environment.root.root if self.windfile.environment else {},
            "needs_lifecycle_parameter": self.needs_lifecycle_parameter,
            "needs_subshells": self.needs_subshells,
            "has_always_actions": self.has_always_actions(),
            "functions": self.functions,
            "steps": [action.root for action in self.windfile.actions],
            "always_steps": [action.root for action in self.windfile.actions if action.root.runAlways],
            "metadata": self.windfile.metadata,
            "before_results": self.before_results,
            "after_results": self.after_results,
        }

        # Render the template with your data
        rendered_script = self.template.render(data)

        return rendered_script

    def generate(self) -> str:
        """
        Generate the bash script to be used as a local CI system. We don't clone the repository here, because
        we don't want to handle the credentials in the CI system.
        :return: bash script
        """
        self.result = ""
        utils.replace_environment_variables_in_windfile(environment=self.environment, windfile=self.windfile)
        self.add_repository_urls_to_environment()
        for step in self.windfile.actions:
            if isinstance(step.root, ScriptAction):
                self.handle_step(name=step.root.name, step=step.root, call=not step.root.runAlways)
        self.result = self.generate_using_jinja2()
        return super().generate()
