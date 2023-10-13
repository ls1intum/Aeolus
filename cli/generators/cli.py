# pylint: disable=duplicate-code
import os
import subprocess
import tempfile
from typing import List, Optional

from classes.generated.definitions import InternalAction, Repository
from generators.base import BaseGenerator
from utils import logger
from docker.models.containers import Container  # type: ignore
from docker.client import DockerClient  # type: ignore
from docker.types.daemon import CancellableStream  # type: ignore


class CliGenerator(BaseGenerator):
    """
    CLI generator. Generates a bash script to be used as a local CI system.
    """

    functions: List[str] = []

    def add_prefix(self) -> None:
        """
        Add the prefix to the bash script.
        E.g. the shebang, some output settings, etc.
        """
        self.result.append("#!/usr/bin/env bash")
        self.result.append("set -e")
        # if self.output_settings.debug:
        #     self.result.append("set -x")
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
        self.result.append("main () " + "{")
        self.result.append('  local _current_lifecycle="${1}"')
        if self.has_always_actions():
            self.result.append("  trap final_aeolus_post_action EXIT")
        for function in self.functions:
            self.result.append(f"  {function} $_current_lifecycle")
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
        self.result.append("  echo '⚙️ executing final_aeolus_post_action'")
        for step in steps:
            self.result.append(f"  {step} $_current_lifecycle")
        self.result.append("}")

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
        if step.excludeDuring is not None:
            # we don't need the local variable if there are no exclusions
            self.result.append('  local _current_lifecycle="${1}"')

            for exclusion in step.excludeDuring:
                self.result.append(f'  if [[ "${{_current_lifecycle}}" == "{exclusion.name}" ]]; then')
                self.result.append(f"    echo '⚠️  {name} is excluded during {exclusion.name}'")
                self.result.append("    return 0")
                self.result.append("  fi")

        self.result.append(f"  echo '⚙️ executing {name}'")
        if step.environment:
            for env_var in step.environment.root.root:
                self.result.append(f'  export {env_var}="' f'{step.environment.root.root[env_var]}"')
        if step.parameters is not None:
            for parameter in step.parameters.root.root:
                self.result.append(f'  {parameter}="{step.parameters.root.root[parameter]}"')
        for line in step.script.split("\n"):
            if line:
                self.result.append(f"  {line}")
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
        clone_method: str = f"clone_{name}"
        self.result.append(f"# step {name}")
        self.result.append(f"# generated from repository {name}")
        self.result.append(f"{clone_method} () " + "{")
        self.result.append(f"  echo '🖨️ cloning {name}'")
        self.result.append(f"  git clone {repository.url} --branch {repository.branch} {directory}")
        self.result.append("}")
        self.functions.append(clone_method)

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
            container_name: str = "aeolus-worker"
            container_image: str = os.getenv("AEOLUS_WORKER_IMAGE", "ghcr.io/ls1intum/aeolus/worker:nightly")
            if self.windfile.metadata.docker is not None:
                container_image = self.windfile.metadata.docker.image + (
                    (":" + self.windfile.metadata.docker.tag) if self.windfile.metadata.docker.tag else ""
                )
            client.containers.run(
                image=container_image,
                command=f"bash /entrypoint.sh {self.output_settings.run_settings.stage}",
                volumes={temp.name: {"bind": "/entrypoint.sh", "mode": "ro"}},
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
        Generate the bash script to be used as a local CI system.
        :return: bash script
        """
        self.add_prefix()
        if self.windfile.repositories:
            for name in self.windfile.repositories:
                repository: Repository = self.windfile.repositories[name]
                self.handle_clone(name, repository)
        for name, step in self.windfile.actions.items():
            if isinstance(step.root, InternalAction):
                self.handle_step(name=name, step=step.root, call=not step.root.run_always)

        if self.has_always_actions():
            always_actions: list[str] = []
            for name, step in self.windfile.actions.items():
                if isinstance(step.root, InternalAction) and step.root.run_always:
                    always_actions.append(name)
            self.handle_always_steps(steps=always_actions)
        self.add_postfix()
        return super().generate()
