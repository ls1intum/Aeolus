import typing
from typing import Optional, Tuple, Any
import re
import yaml

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
)
from classes.bamboo_client import BambooClient
from classes.ci_credentials import CICredentials
from classes.generated.definitions import (
    Target,
    WindfileMetadata,
    InternalAction,
    Repository,
    Docker,
    Api,
    Author,
    Environment,
    Lifecycle,
    Action,
    Dictionary,
    PlatformAction,
    FileAction,
    ExternalAction,
    Parameters,
)
from classes.generated.environment import EnvironmentSchema
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.pass_settings import PassSettings
from utils import logger, utils


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


def parse_env_variables(environment: EnvironmentSchema, variables: dict[Any, str | float | None]) -> Environment:
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
    param_dictionary: dict[Any, str | float | bool | None] = {}
    for value in task.arguments:
        param_dictionary[value] = utils.replace_bamboo_environment_variable_with_aeolus(
            environment=environment, haystack=value
        )
    if isinstance(task, BambooSpecialTask):
        for key, value in task.parameters.items():
            updated: str | float | bool | None = value
            if isinstance(value, str):
                updated = utils.replace_bamboo_environment_variable_with_aeolus(
                    environment=environment, haystack=updated
                )
            param_dictionary[key] = updated
    print(param_dictionary)
    return Parameters(root=Dictionary(root=param_dictionary))


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
            action = Action(
                root=PlatformAction(
                    parameters=params,
                    kind=task.task_type,
                    excludeDuring=exclude,
                    file=None,
                    function=None,
                    docker=docker,
                    environment=envs,
                    platform=Target.bamboo,
                    run_always=task.always_execute,
                )
            )
    else:
        script: str = "".join(task.scripts)
        action = Action(
            root=InternalAction(
                script="".join(
                    utils.replace_bamboo_environment_variable_with_aeolus(environment=environment, haystack=script)
                ),
                excludeDuring=exclude,
                docker=docker,
                parameters=params,
                environment=envs,
                platform=None,
                run_always=task.always_execute,
            )
        )
    return action


def extract_actions(stages: dict[str, BambooStage], environment: EnvironmentSchema) -> dict[Any, Action]:
    """
    Converts all jobs and tasks from the given stages (from the REST API)
    into a dictionary of InternalActions.
    :param stages: dict of stages from the REST API
    :param environment: Environment variables from the REST API
    :return: dict of InternalActions
    """
    actions: dict[Any, Action] = {}
    for _, stage in stages.items():
        for job_name in stage.jobs:
            job: BambooJob = stage.jobs[job_name]
            counter: int = 0
            for task in job.tasks:
                if isinstance(task, BambooTask):
                    counter += 1
                    action: Optional[Action] = extract_action(job=job, task=task, environment=environment)
                    if action is not None:
                        actions[job.key.lower() + str(counter)] = action
    return actions


def clean_up(windfile: WindFile) -> None:
    """
    Removes empty environment and parameters from the given windfile.
    :param windfile:
    """
    for action in windfile.actions:
        root_action: FileAction | InternalAction | PlatformAction | ExternalAction = windfile.actions[action].root
        if root_action.environment is not None and len(root_action.environment.root.root) == 0:
            root_action.environment = None
        if root_action.parameters is not None and len(root_action.parameters.root.root) == 0:
            root_action.parameters = None
        if root_action.excludeDuring is not None and len(root_action.excludeDuring) == 0:
            root_action.excludeDuring = None


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
        for _, action in windfile.actions.items():
            if isinstance(action.root, InternalAction):
                action.root.script = utils.replace_bamboo_environment_variable_with_aeolus(
                    environment=self.environment, haystack=action.root.script
                )

    def combine_docker_config(self, windfile: WindFile) -> None:
        """
        Checks if all docker configurations are identical. If a bamboo plan is
        configured to be run in docker, the docker configuration can be equal
        in every action. So we can move the docker configuration to the metadata to make it easier to read.
        :param windfile: Windfile to check
        """
        docker_configs: dict[str, Optional[Docker]] = {}
        for action in windfile.actions:
            docker_configs[action] = windfile.actions[action].root.docker
        first: Optional[Docker] = list(docker_configs.values())[0]
        are_identical: bool = True
        for _, config in docker_configs.items():
            if first != config:
                logger.info("🚧", "Docker configurations are not identical", self.output_settings.emoji)
                are_identical = False
                break
        if are_identical:
            logger.info("🚀", "Docker configurations are identical", self.output_settings.emoji)
            windfile.metadata.docker = first
            for action in windfile.actions:
                windfile.actions[action].root.docker = None

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
        actions: dict[Any, Action] = extract_actions(stages=specs.stages, environment=self.environment)
        repositories: dict[str, Repository] = extract_repositories(stages=specs.stages, repositories=specs.repositories)
        metadata: WindfileMetadata = WindfileMetadata(
            name=plan.name,
            description=plan.description,
            author=Author(root="bamboo"),
            id=plan_key,
            docker=None,
            targets=None,
            gitCredentials=specs.repositories[list(specs.repositories.keys())[0]].shared_credentials,
        )
        windfile: WindFile = WindFile(
            api=Api(root="v0.0.1"), metadata=metadata, actions=actions, repositories=repositories
        )
        self.combine_docker_config(windfile=windfile)
        clean_up(windfile=windfile)
        # work-around as enums do not get cleanly printed with model_dump
        json: str = windfile.model_dump_json(exclude_none=True)
        logger.info("🪄", "Translated windfile", self.output_settings.emoji)
        print(yaml.dump(yaml.safe_load(json), sort_keys=False))
        return None
