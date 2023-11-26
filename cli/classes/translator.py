"""
This file contains the translator for Bamboo. It converts the reponse of the Bamboo REST API into a Windfile.
"""
import re
import typing
from typing import Optional, Tuple, Any

import yaml

from classes.bamboo_client import BambooClient
from classes.bamboo_specs import (
    BambooSpecs,
    BambooPlan,
    BambooJob,
    BambooStage,
    BambooCheckoutTask,
    BambooTask,
    BambooRepository,
    BambooSpecialTask,
    BambooDockerConfig,
    BambooArtifact,
)
from classes.ci_credentials import CICredentials
from classes.generated.definitions import (
    Target,
    WindfileMetadata,
    ScriptAction,
    Repository,
    Docker,
    Api,
    Author,
    Environment,
    Lifecycle,
    Action,
    Dictionary,
    PlatformAction,
    Parameters,
    Result,
)
from classes.generated.environment import EnvironmentSchema
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.pass_settings import PassSettings
from classes.yaml_dumper import YamlDumper
from cli_utils import logger, utils


def parse_docker(docker_config: Optional[BambooDockerConfig], environment: EnvironmentSchema) -> Optional[Docker]:
    """
    Converts the given docker configuration into a Docker object.
    :param docker_config: Config from Bamboo
    :param environment: Environment variables to replace
    :return: Docker object or None
    """
    if docker_config is not None:
        volume_list: list[str] = []
        for volume in docker_config.volumes:
            host: str = utils.replace_bamboo_environment_variable_with_aeolus(environment=environment, haystack=volume)
            container: str = utils.replace_bamboo_environment_variable_with_aeolus(
                environment=environment, haystack=docker_config.volumes[volume]
            )
            volume_list.append(f"{host}:{container}")
        arguments: list[str] = utils.replace_bamboo_environment_variables_with_aeolus(
            environment=environment, haystack=docker_config.docker_run_arguments
        )
        docker = Docker(
            image=docker_config.image if ":" not in docker_config.image else docker_config.image.split(":")[0],
            tag=docker_config.image.split(":")[1] if ":" in docker_config.image else "latest",
            volumes=volume_list,
            parameters=arguments,
        )
        return docker
    return None


def parse_env_variables(
    environment: EnvironmentSchema, variables: dict[Any, int | str | float | bool | list[Any] | None]
) -> Environment:
    """
    Converts the given environment variables into a Environment object.
    :param environment: Environment variables to replace
    :param variables: Environment variables from Bamboo
    :return:
    """
    dictionary: Dictionary = Dictionary(root={})
    for key, value in variables.items():
        dictionary.root[key] = (
            utils.replace_bamboo_environment_variable_with_aeolus(environment=environment, haystack=value)
            if isinstance(value, str)
            else value
        )
    return Environment(root=dictionary)


def parse_arguments(environment: EnvironmentSchema, task: BambooTask) -> Parameters:
    """
    Converts the given arguments into a Parameters object.
    :param environment: Environment variables to replace
    :param task: Task containing the arguments
    :return: Parameters object
    """
    param_dictionary: dict[Any, str | float | bool | list | None] = {}
    for value in task.arguments:
        param_dictionary[value] = utils.replace_bamboo_environment_variable_with_aeolus(
            environment=environment, haystack=value
        )
    if isinstance(task, BambooSpecialTask):
        for key in task.parameters:
            if key in ["working_dir"]:
                continue
            updated: Optional[str | float | bool | list] = task.parameters[key]
            if task.task_type == "maven":
                # clean up unnecessary parameters
                if key in ["executable", "jdk", "goal", "tests"]:
                    continue
            if isinstance(updated, str):
                updated = utils.replace_bamboo_environment_variable_with_aeolus(
                    environment=environment, haystack=updated
                )
            param_dictionary[key] = updated
    return Parameters(root=Dictionary(root=param_dictionary))


def extract_action_name(task: BambooTask) -> str:
    """
    Extracts the name of the given task of the given Job.
    :param task: Task to convert
    :return: name of the task
    """
    if isinstance(task, BambooSpecialTask):
        return task.task_type
    if isinstance(task, BambooTask):
        return task.description.replace(" ", "_").lower()
    return task.description.replace(" ", "_").lower()


def extract_action(job: BambooJob, task: BambooTask, environment: EnvironmentSchema) -> Optional[Action]:
    """
    Converts the given task of the given Job into an Action.
    Setting the conditions and environment variables fetched from Bamboo
    :param job: Job containing the task we want to convert
    :param task: Task to convert
    :param environment: Environment variables to replace
    :return: converted Action
    """
    exclude: list[Lifecycle] = []
    if task.condition is not None:
        for condition in task.condition.variables:
            for match in condition.matches:
                regex = re.compile(r"[^a-zA-Z |_]")
                lifecycle = condition.matches[match]
                for entry in regex.sub("", lifecycle).split("|"):
                    exclude.append(Lifecycle[entry])
    docker: Optional[Docker] = parse_docker(docker_config=job.docker, environment=environment)
    envs: Environment = parse_env_variables(environment=environment, variables=task.environment)
    params: Parameters = parse_arguments(environment=environment, task=task)
    action: Optional[Action] = None
    if isinstance(task, BambooSpecialTask):
        if isinstance(task, BambooSpecialTask):
            if task.task_type == "maven":
                action = Action(  # type: ignore
                    ScriptAction(
                        name=extract_action_name(task=task),
                        script=f"mvn {task.goal}",
                        excludeDuring=exclude,
                        workdir=str(task.parameters["working_dir"]) if "working_dir" in task.parameters else None,
                        docker=docker,
                        parameters=params,
                        environment=envs,
                        results=None,
                        platform=None,
                        runAlways=task.always_execute,
                    )
                )
            else:
                action = Action(
                    root=PlatformAction(
                        name=extract_action_name(task=task),
                        parameters=params,
                        kind=task.task_type,
                        excludeDuring=exclude,
                        workdir=str(task.parameters["working_dir"]) if "working_dir" in task.parameters else None,
                        file=None,
                        function=None,
                        docker=docker,
                        results=None,
                        environment=envs,
                        platform=Target.bamboo,
                        runAlways=task.always_execute,
                    )
                )
    else:
        script: str = "".join(task.scripts)
        code: str = utils.replace_bamboo_environment_variable_with_aeolus(environment=environment, haystack=script)
        code = code.lstrip('"').rstrip('"')
        action = Action(
            root=ScriptAction(
                name=task.description.replace(" ", "_").lower(),
                script=code,
                excludeDuring=exclude,
                workdir=task.workdir if task.workdir else None,
                docker=docker,
                parameters=params,
                environment=envs,
                results=None,
                platform=None,
                runAlways=task.always_execute,
            )
        )
    return action


def convert_results(artifacts: typing.List[BambooArtifact]) -> typing.List[Result]:
    """
    Convert the artifacts from the Bamboo response into easy to work with objects.
    :param artifacts: list of artifacts from Bamboo
    :return: list of BambooArtifact objects
    """
    results: list[Result] = []
    for artifact in artifacts:
        results.append(
            Result(
                name=artifact.name,
                path=artifact.location + "/" + artifact.pattern,
                ignore=artifact.exclusion,
                type=None,
            )
        )
    return results


def convert_junit_tasks_to_results(actions: list[Action], homeless_junit_actions: list[PlatformAction]) -> None:
    """
    Converts the given list of junit tasks into a list of results.
    :param homeless_junit_actions: list of junit tasks
    """
    for junit_action in homeless_junit_actions:
        if len(actions) > 0:
            paths: list[str] = []
            if (
                  junit_action.parameters is None or
                  junit_action.parameters.root is None or
                  junit_action.parameters.root.root is None or
                  junit_action.parameters.root.root["test_results"] is None
            ):
                # we don't want to add empty junit actions with no parameter test_results
                continue
            if isinstance(junit_action.parameters.root.root["test_results"], list):
                paths = junit_action.parameters.root.root["test_results"]
            elif isinstance(junit_action.parameters.root.root["test_results"], str):
                paths.append(junit_action.parameters.root.root["test_results"])
            results: list[Result] = []
            for path in paths:
                results.append(Result(name=f"{junit_action.name}_{path}", path=path, type="junit", ignore=None))
            could_be_added: bool = False
            for i, element in reversed(list(enumerate(actions))):
                if isinstance(element.root, ScriptAction):
                    if (
                          element.root.excludeDuring == junit_action.excludeDuring
                          and element.root.runAlways == junit_action.runAlways
                          and element.root.workdir == junit_action.workdir
                    ):
                        could_be_added = True
                        if element.root.results is None:
                            element.root.results = results
                        else:
                            for result in results:
                                element.root.results.append(result)
                        break
            if not could_be_added:
                actions.append(
                    Action(
                        root=ScriptAction(
                            name=junit_action.name,
                            script="#empty script action, just for the results",
                            excludeDuring=junit_action.excludeDuring,
                            workdir=junit_action.workdir,
                            docker=junit_action.docker,
                            parameters=None,
                            environment=None,
                            results=results,
                            platform=None,
                            runAlways=junit_action.runAlways,
                        )
                    )
                )

def extract_actions(stages: dict[str, BambooStage], environment: EnvironmentSchema) -> list[Action]:
    """
    Converts all jobs and tasks from the given stages (from the REST API)
    into a dictionary of ScriptActions.
    :param stages: dict of stages from the REST API
    :param environment: Environment variables from the REST API
    :return: dict of ScriptActions
    """
    actions: list[Action] = []
    for _, stage in stages.items():
        for job_name in stage.jobs:
            job: BambooJob = stage.jobs[job_name]
            homeless_junit_actions: list[PlatformAction] = []
            for task in job.tasks:
                if isinstance(task, BambooTask):
                    action: Optional[Action] = extract_action(job=job, task=task, environment=environment)
                    if action is not None:
                        if isinstance(action.root, PlatformAction) and action.root.kind in ("junit", "test_parser"):
                            homeless_junit_actions.append(action.root)
                        else:
                            actions.append(action)
            # we have a different abstraction for artifacts, so we simply append them to the last action
            if job.artifacts is not None:
                if len(actions) > 0:
                    actions[-1].root.results = convert_results(job.artifacts)
            # we also don't want any orphaned junit actions, so we add them to the last action with the same
            # excludeDuring and runAlways
            convert_junit_tasks_to_results(actions=actions, homeless_junit_actions=homeless_junit_actions)

    return actions


def extract_repositories(
    stages: dict[str, BambooStage], repositories: dict[str, BambooRepository]
) -> dict[str, Repository]:
    """
    Extracts the repositories from the given stages. So we can add them to the windfile.
    :param stages: stages that possibly contain repositories in its tasks
    :param repositories: repositories defined in the Build Plan
    :return: dict of parsed repositories
    """
    found: dict[str, Repository] = {}
    for _, stage in stages.items():
        for job_name in stage.jobs:
            job: BambooJob = stage.jobs[job_name]
            for task in job.tasks:
                if isinstance(task, BambooCheckoutTask):
                    checkout: BambooCheckoutTask = task
                    repository: Repository = Repository(
                        url=repositories[checkout.repository].url,
                        branch=repositories[checkout.repository].branch,
                        path=checkout.path,
                    )
                    found[checkout.repository] = repository
    return found


class BambooTranslator(PassSettings):
    source: Target = Target.bamboo
    client: BambooClient
    environment: EnvironmentSchema

    def __init__(self, input_settings: InputSettings, output_settings: OutputSettings, credentials: CICredentials):
        input_settings.target = Target.bamboo
        env: typing.Optional[EnvironmentSchema] = utils.get_ci_environment(
            target=input_settings.target, output_settings=output_settings
        )
        if env is None:
            raise ValueError(f"No environment found for target {input_settings.target.value}")
        self.environment = env
        super().__init__(input_settings=input_settings, output_settings=output_settings)
        self.client = BambooClient(credentials=credentials)

    def replace_environment_variables(self, windfile: WindFile) -> None:
        """
        Replaces the environment variables in the given windfile.
        :param windfile: Windfile to replace
        """
        if windfile.metadata.docker is not None:
            windfile.metadata.docker.volumes = utils.replace_bamboo_environment_variables_with_aeolus(
                environment=self.environment, haystack=windfile.metadata.docker.volumes
            )
            windfile.metadata.docker.parameters = utils.replace_bamboo_environment_variables_with_aeolus(
                environment=self.environment, haystack=windfile.metadata.docker.parameters
            )
        for action in windfile.actions:
            if isinstance(action.root, ScriptAction):
                action.root.script = utils.replace_bamboo_environment_variable_with_aeolus(
                    environment=self.environment, haystack=action.root.script
                )

    def translate(self, plan_key: str) -> Optional[WindFile]:
        """
        Translate the given build plan into a windfile.
        :return: Windfile
        """
        optional: Optional[Tuple[BambooSpecs, dict[str, Any]]] = self.client.get_plan_yaml(plan_key=plan_key)
        if optional is None:
            return None
        specs: BambooSpecs = optional[0]
        # raw: dict[str, str] = optional[1]
        plan: BambooPlan = specs.plan
        actions: list[Action] = extract_actions(stages=specs.stages, environment=self.environment)
        repositories: dict[str, Repository] = extract_repositories(stages=specs.stages, repositories=specs.repositories)
        metadata: WindfileMetadata = WindfileMetadata(
            name=plan.name,
            description=plan.description,
            author=Author(root="bamboo"),
            id=plan_key,
            docker=None,
            targets=None,
            gitCredentials=specs.repositories[list(specs.repositories.keys())[0]].shared_credentials,
            resultHook=None,
        )
        windfile: WindFile = WindFile(
            api=Api(root="v0.0.1"), metadata=metadata, actions=actions, repositories=repositories
        )
        utils.clean_up(windfile=windfile, output_settings=self.output_settings)
        # work-around as enums do not get cleanly printed with model_dump
        json: str = windfile.model_dump_json(exclude_none=True)
        logger.info("🪄", "Translated windfile", self.output_settings.emoji)
        print(yaml.dump(yaml.safe_load(json), sort_keys=False, Dumper=YamlDumper, default_flow_style=False))
        return windfile
