# pylint: disable=duplicate-code
"""
Bamboo generator. Because bamboo works differently to other CI systems, we can not directly generate the YAML Spec
file. Instead, support multiple ways of generating the YAML Spec file:
- we are in a docker container and can not use the provided bamboo-generator container, so we need to call the java jar
directly (most convenient)
- we are not in a docker container and can use the provided bamboo-generator container, so we call docker (fastest)
- we are not in a docker container and can not use the provided bamboo-generator container, so we call the java
jar directly (slowest)
"""
import base64
import json
import os
import subprocess
import time
from typing import List, Any, Optional

import requests
from docker.client import DockerClient  # type: ignore
from docker.errors import DockerException  # type: ignore
from docker.models.containers import Container  # type: ignore
from docker.types.daemon import CancellableStream  # type: ignore

import cli_utils
from classes.generated.definitions import Target
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.pass_metadata import PassMetadata
from cli_utils import logger, utils
from generators.base import BaseGenerator


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

    def __init__(
        self, windfile: WindFile, input_settings: InputSettings, output_settings: OutputSettings, metadata: PassMetadata
    ):
        input_settings.target = Target.bamboo
        super().__init__(windfile, input_settings, output_settings, metadata)

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
        start = time.time()
        utils.replace_environment_variables_in_windfile(environment=self.environment, windfile=self.windfile)
        end = time.time()
        cli_utils.logger.info("🔨", f"Replaced environment variables in {end - start}s", self.output_settings.emoji)
        logger.info("🔨", "Generating Bamboo YAML Spec file...", self.output_settings.emoji)

        json_windfile: str = self.windfile.model_dump_json(exclude_none=True)
        start = time.time()
        self.key = self.generate_in_api(payload=json_windfile)
        if not self.key:
            # we use base64 a base64 encoded json string, so we do not have to handle any escaping
            escaped: str = base64.b64encode(json_windfile.encode("utf-8")).decode("utf-8")
            if docker_available():
                logger.debug("🐳", "Docker is available, using docker container", self.output_settings.emoji)
                self.generate_in_docker(base64_str=escaped)
            else:
                logger.debug("☕️", "Docker is not available, using java jar", self.output_settings.emoji)
                self.generate_in_java(base64_str=escaped)
        end = time.time()
        cli_utils.logger.info("🔨", f"Generated Bamboo YAML Spec file in {end - start}s", self.output_settings.emoji)
        return super().generate()

    def generate_in_api(self, payload: str) -> Optional[str]:
        """
        Generate the bamboo specs that can be used to create a plan in bamboo. We call the REST API, this is
        faster than calling the docker container or starting the java jar.
        :param payload: json string of the windfile definition
        :return key of the generated bamboo plan
        """
        try:
            host: str = os.getenv("BAMBOO_GENERATOR_API_HOST", "http://localhost:8080")
            endpoint: str = f"{host}/generate"
            data: dict[str, Optional[str]] = {"windfile": payload}

            if self.output_settings.ci_credentials is not None:
                endpoint = f"{host}/publish"
                data["url"] = self.output_settings.ci_credentials.url
                data["token"] = self.output_settings.ci_credentials.token
                data["username"] = self.output_settings.ci_credentials.username

            headers: dict[str, str] = {"Content-Type": "application/json"}
            response = requests.post(endpoint, headers=headers, data=json.dumps(data), timeout=30)
            if response.status_code == 200:
                logger.info("🔨", "Bamboo YAML Spec file generated", self.output_settings.emoji)
                body: dict[str, str] = response.json()
                self.result.append(body["result"])
                return body["key"]
            logger.error("❌", "Bamboo YAML Spec file generation failed", self.output_settings.emoji)
            raise ValueError("Bamboo YAML Spec file generation failed")
        except requests.exceptions.ConnectionError:
            return None

    def generate_in_java(self, base64_str: str) -> None:
        """
        Generate the bamboo specs that can be used to create a plan in bamboo. We call the java jar directly, this is
        intended for when we are in a docker container and can not use the provided bamboo-generator container.
        :param base64_str: windfile definition as base64 encoded string
        """
        command: List[str] = ["java", "-jar", "bamboo-generator.jar", "--base64", base64_str]
        if self.output_settings.ci_credentials is not None:
            command += [
                "--server",
                self.output_settings.ci_credentials.url,
                "--token",
                self.output_settings.ci_credentials.token,
            ]
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
        command: str = f"--base64 {base64_str}"
        if self.output_settings.ci_credentials is not None:
            command += f" --publish --server {self.output_settings.ci_credentials.url} "
            command += f"--token {self.output_settings.ci_credentials.token}"
        client.containers.run(
            image=os.getenv("BAMBOO_GENERATOR_IMAGE", "ghcr.io/ls1intum/aeolus/bamboo-generator:nightly"),
            command=f"{command}",
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
        result: dict[Any, Any] = container.wait()
        if result["StatusCode"] != 0:
            logger.error("❌", "Bamboo YAML Spec file generation failed", self.output_settings.emoji)
            container.remove()
            raise ValueError("Bamboo YAML Spec file generation failed")
        logger.info("🔨", "Bamboo YAML Spec file generated", self.output_settings.emoji)
        result_logs: str = container.logs(stdout=True, stderr=False).decode("utf-8")
        container.remove()
        self.result.append(result_logs)

    def check(self, content: str) -> bool:
        raise NotImplementedError("check_syntax() not implemented")

    def run(self, job_id: str) -> None:
        if self.output_settings.run_settings is None or self.output_settings.ci_credentials is None:
            return
        if self.final_result is None:
            return
        build_id: str = job_id.replace("/", "-").upper()
        logger.info("🔨", f"Triggering Bamboo build for {build_id}", self.output_settings.emoji)

        # Endpoint to trigger the build
        endpoint: str = f"{self.output_settings.ci_credentials.url}/rest/api/latest/queue/{build_id}"

        # Make the request
        headers: dict[str, str] = {"Authorization": f"Bearer {self.output_settings.ci_credentials.token}"}
        params: dict[str, str] = {"bamboo.variable.lifecycle_stage": str(self.output_settings.run_settings.stage)}
        response = requests.post(endpoint, headers=headers, params=params, timeout=30)

        # Check the response
        if response.status_code == 200:
            logger.info("🔨", f"Triggered Bamboo build for {build_id} successfully", self.output_settings.emoji)
        else:
            logger.error(
                "❌",
                f"Failed to trigger Bamboo build for {build_id}, got {response.status_code}",
                self.output_settings.emoji,
            )
