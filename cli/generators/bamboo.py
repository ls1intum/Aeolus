# pylint: disable=duplicate-code
import base64
import subprocess
from typing import List
from utils import logger

from generators.base import BaseGenerator
from docker.models.containers import Container  # type: ignore
from docker.client import DockerClient  # type: ignore
from docker.errors import DockerException  # type: ignore
from docker.types.daemon import CancellableStream  # type: ignore


def docker_available() -> bool:
    """
    Check if docker is available
    :return:
    """
    try:
        DockerClient.from_env()
        return True
    except DockerException:
        return False


class BambooGenerator(BaseGenerator):
    """
    Jenkins generator. Because bamboo works differently to other CI systems,
    we call a docker container that generates the Bamboo YAML Spec file and
    can directly publish the plan to the Bamboo server.
    """

    def generate(self) -> str:
        """
        Generate the bamboo specs that can be used to create a plan in bamboo.
        We need to cover the following cases:
        - we are in a docker container and can not use the provided bamboo-generator container,
        so we need to call the java jar directly
        - we are not in a docker container and can use the provided bamboo-generator container,
        so we simply call docker
        :return: bamboo yaml specs
        """
        logger.info("🔨", "Generating Bamboo YAML Spec file...", self.output_settings.emoji)

        json: str = self.windfile.model_dump_json(exclude_none=True)
        # we use base64 a base64 encoded json string, so we do not have to handle any escaping
        escaped: str = base64.b64encode(json.encode("utf-8")).decode("utf-8")
        if docker_available():
            logger.debug("🐳", "Docker is available, using docker container", self.output_settings.emoji)
            self.generate_in_docker(base64_str=escaped)
        else:
            logger.debug("☕️", "Docker is not available, using java jar", self.output_settings.emoji)
            self.generate_in_java(base64_str=escaped)
        return super().generate()

    def generate_in_java(self, base64_str: str) -> None:
        """
        Generate the bamboo specs that can be used to create a plan in bamboo. We call the java jar directly, this is
        intended for when we are in a docker container and can not use the provided bamboo-generator container.
        :param base64_str: windfile definition as base64 encoded string
        """
        command: List[str] = ["java", "-jar", "bamboo-generator.jar", "--base64", base64_str]
        process: subprocess.CompletedProcess = subprocess.run(command, text=True, capture_output=True, check=True)
        error_logs: str = process.stderr.split("\n")
        for error_log in error_logs:
            if error_log:
                logger.info("☕️", error_log, self.output_settings.emoji)
        if process.returncode != 0:
            logger.error("❌", "Bamboo YAML Spec file generation failed", self.output_settings.emoji)
            raise ValueError("Bamboo YAML Spec file generation failed")
        logger.info("🔨", "Bamboo YAML Spec file generated", self.output_settings.emoji)
        result_logs: str = process.stdout
        self.result.append(result_logs)

    def generate_in_docker(self, base64_str: str) -> None:
        """
        Generate the bamboo specs that can be used to create a plan in bamboo. We call the docker container, this is
        intended for when we are not in a docker container and can use the provided bamboo-generator container.
        :param base64_str: windfile definition as base64 encoded string
        """
        client: DockerClient = DockerClient.from_env()
        container_name: str = "bambeolus"
        client.containers.run(
            image="ghcr.io/ls1intum/aeolus/bamboo-generator",
            command=f"--base64 {base64_str}",
            auto_remove=False,
            name=container_name,
            detach=True,
        )
        container: Container = client.containers.get(container_name)
        error_logs: CancellableStream = container.logs(stream=True, stdout=False, stderr=True)
        # we expect only the result in stdout, everything else (including logs) is in stderr
        while container.status == "running":
            try:
                lines: List[str] = error_logs.next().decode("utf-8").split("\n")
                for line in lines:
                    if line:
                        logger.info("🐳", line, self.output_settings.emoji)
            except StopIteration:
                break
        logger.info("🔨", "Bamboo YAML Spec file generated", self.output_settings.emoji)
        result_logs: str = container.logs(stdout=True, stderr=False).decode("utf-8")
        container.remove()
        self.result.append(result_logs)

    def check(self, content: str) -> bool:
        raise NotImplementedError("check_syntax() not implemented")
