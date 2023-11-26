# pylint: disable=duplicate-code
import os
import subprocess
import tempfile
import typing
from typing import List, Optional

from docker.client import DockerClient  # type: ignore
from docker.models.containers import Container  # type: ignore
from docker.types.daemon import CancellableStream  # type: ignore

from classes.generated.definitions import ScriptAction, Repository, Target, Lifecycle
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

    def __init__(
        self, windfile: WindFile, input_settings: InputSettings, output_settings: OutputSettings, metadata: PassMetadata
    ):
        input_settings.target = Target.cli
        self.functions = []
        super().__init__(windfile, input_settings, output_settings, metadata)

    def add_prefix(self) -> None:
        """
        Add the prefix to the bash script.
        E.g. the shebang, some output settings, etc.
        """
        self.result.append("#!/usr/bin/env bash")
        self.result.append("set -e")

        # actions could run in a different directory, so we need to store to the initial directory
        self.result.append(f"export {self.initial_directory_variable}=$(pwd)")

        # to work with jenkins and bamboo, we need a way to access the repository url, as this is not possible
        # in a scripted jenkins pipeline, we set it as an environment variable
        self.add_repository_urls_to_environment()

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
        self.result.append("main () {")
        self.add_line(indentation=2, line='local _current_lifecycle="${1}"')
        if self.has_always_actions() or self.has_results():
            self.add_line(indentation=2, line="trap final_aeolus_post_action EXIT")
        for function in self.functions:
            self.add_line(indentation=2, line=f"{function} $_current_lifecycle")
            self.add_line(indentation=2, line=f"cd ${self.initial_directory_variable}")
        self.result.append("}\n")
        self.result.append("main $@")

    def handle_always_steps(self, steps: list[str]) -> None:
        """
        Translate a step into a CI post action.
        :param steps: to call always
        :return: CI action
        """
        self.result.append("\n# always steps")
        self.result.append("final_aeolus_post_action () " + "{")
        self.add_line(indentation=2, line="set +e # from now on, we don't exit on errors")
        self.add_line(indentation=2, line="echo '⚙️ executing final_aeolus_post_action'")
        self.add_line(indentation=2, line=f"cd ${self.initial_directory_variable}")
        for step in steps:
            self.add_line(indentation=2, line=f"{step} $_current_lifecycle")
            self.add_line(indentation=2, line=f"cd ${self.initial_directory_variable}")
        self.result.append("}")

    def add_lifecycle_guards(self, name: str, exclusions: Optional[List[Lifecycle]], indentations: int = 2) -> None:
        """
        Add lifecycle guards to the given action.
        :param name: name of the action
        :param exclusions: list of lifecycle exclusions
        :param indentations: number of indentations
        """
        if exclusions is not None:
            # we don't need the local variable if there are no exclusions
            self.add_line(indentation=indentations, line='local _current_lifecycle="${1}"')

            for exclusion in exclusions:
                self.add_line(
                    indentation=indentations, line=f'if [[ "${{_current_lifecycle}}" == "{exclusion.name}" ]]; then'
                )
                indentations += 2
                self.add_line(
                    indentation=indentations, line="echo '⚠️  " f"{name} is excluded during {exclusion.name}'"
                )
                self.add_line(indentation=indentations, line="return 0")
                indentations -= 2
                self.add_line(indentation=indentations, line="fi")

    def handle_results(self) -> None:
        """
        https://askubuntu.com/a/889746
        https://stackoverflow.com/a/8088439
        Handle the results of all steps
        """
        self.result.append("\n# move results")
        self.result.append("aeolus_move_results () " + "{")
        self.add_line(indentation=2, line="echo '⚙️ moving results'")
        self.add_line(indentation=2, line="mkdir -p /aeolus-results")
        self.add_line(indentation=2, line="shopt -s extglob")
        for workdir, entries in self.results.items():
            self.add_line(indentation=2, line=f"cd {workdir}")
            for result in entries:
                self.add_line(indentation=2, line=f'local _sources="{result.path}"')
                if result.ignore:
                    self.add_line(indentation=2, line=f"_sources=$(echo $_sources/!({result.ignore}))")
                self.add_line(indentation=2, line=f"mv $_sources /aeolus-results/{result.path}")
        self.result.append("}")

    def handle_step_results(self, workdir: Optional[str], step: ScriptAction) -> None:
        """
        Process the results of a step.
        :param workdir: working directory of the step
        :param step: object to process
        """
        key: str = workdir if workdir else f"${self.initial_directory_variable}"
        if step.results:
            for result in step.results:
                self.add_result(workdir=key, result=result)

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
            logger.info(
                "🔨",
                "Platform action detected. Skipping...",
                self.output_settings.emoji,
            )
            return None
        self.result.append(f"# step {name}")
        self.result.append(f"# generated from step {original_name}")
        self.result.append(f"# original type was {original_type}")
        if call:
            self.functions.append(name)
        self.result.append(f"{name} () " + "{")
        self.add_lifecycle_guards(name=name, exclusions=step.excludeDuring, indentations=2)

        self.add_line(indentation=2, line="echo '⚙️ executing " f"{name}'")
        self.handle_step_results(workdir=step.workdir, step=step)
        if step.workdir:
            self.add_line(indentation=2, line=f"cd {step.workdir}")
        if step.environment:
            for env_var in step.environment.root.root:
                env_value: typing.Any = step.environment.root.root[env_var]
                if isinstance(env_value, List):
                    env_value = " ".join(env_value)
                self.result.append(f'export {env_var}="' f'{env_value}"')
        if step.parameters is not None:
            for parameter in step.parameters.root.root:
                value: typing.Any = step.parameters.root.root[parameter]
                if isinstance(value, List):
                    value = " ".join(value)
                self.add_line(indentation=2, line=f'{parameter}="' f'{value}"')
        for line in step.script.split("\n"):
            if line:
                self.add_line(indentation=2, line=line)
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
                    logger.error("❌ ", stderr, self.output_settings.emoji)
                if stdout:
                    logger.error("❌ ", stdout, self.output_settings.emoji)
            return has_passed

    def handle_clone(self, name: str, repository: Repository) -> None:
        """
        Handles the clone step.
        :param name: Name of the step
        :param repository: Repository
        """
        directory: str = repository.path
        self.result.append(f"# the repository {name} is expected to be mounted into the container at /{directory}")

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

    def generate(self) -> str:
        """
        Generate the bash script to be used as a local CI system. We don't clone the repository here, because
        we don't want to handle the credentials in the CI system.
        :return: bash script
        """
        utils.replace_environment_variables_in_windfile(environment=self.environment, windfile=self.windfile)
        self.add_prefix()
        if self.windfile.repositories:
            for name in self.windfile.repositories:
                repository: Repository = self.windfile.repositories[name]
                self.handle_clone(name, repository)
        for step in self.windfile.actions:
            if isinstance(step.root, ScriptAction):
                self.handle_step(name=step.root.name, step=step.root, call=not step.root.runAlways)
        if self.has_results():
            self.handle_results()
        if self.has_always_actions() or self.has_results():
            always_actions: list[str] = []
            for step in self.windfile.actions:
                if isinstance(step.root, ScriptAction) and step.root.runAlways:
                    always_actions.append(step.root.name)
            if self.has_results():
                always_actions.append("aeolus_move_results")
            self.handle_always_steps(steps=always_actions)
        self.add_postfix()
        return super().generate()
