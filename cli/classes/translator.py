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
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.pass_settings import PassSettings
from utils import logger


def extract_action(job: BambooJob, task: BambooTask) -> Optional[Action]:
    """
    Converts the given task of the given Job into an Action.
    Setting the conditions and environment variables fetched from Bamboo
    :param job: Job containing the task we want to convert
    :param task: Task to convert
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
    script_task: BambooTask = task
    docker: Optional[Docker] = None
    if job.docker is not None:
        volume_list: list[str] = []
        for volume in job.docker.volumes:
            volume_list.append(f"{volume}:{job.docker.volumes[volume]}")
        docker = Docker(
            image=job.docker.image if ":" not in job.docker.image else job.docker.image.split(":")[0],
            tag=job.docker.image.split(":")[1] if ":" in job.docker.image else "latest",
            volumes=volume_list,
            parameters=job.docker.docker_run_arguments,
        )
    environment: Environment = Environment(root=Dictionary(root=script_task.environment))
    action: Optional[Action] = None
    if isinstance(task, BambooSpecialTask):
        if isinstance(task, BambooSpecialTask):
            action = Action(
                root=PlatformAction(
                    parameters=Parameters(root=Dictionary(root=task.parameters)),
                    kind=task.task_type,
                    excludeDuring=exclude,
                    file=None,
                    function=None,
                    docker=docker,
                    environment=environment,
                    platform=Target.bamboo,
                    always=task.always_execute,
                )
            )
    else:
        action = Action(
            root=InternalAction(
                script="\n".join(script_task.scripts),
                excludeDuring=exclude,
                docker=docker,
                environment=environment,
                platform=None,
                always=task.always_execute,
            )
        )
    return action


def extract_actions(stages: dict[str, BambooStage]) -> dict[Any, Action]:
    """
    Converts all jobs and tasks from the given stages (from the REST API)
    into a dictionary of InternalActions.
    :param stages: dict of stages from the REST API
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
                    action: Optional[Action] = extract_action(job=job, task=task)
                    if action is not None:
                        actions[job.key + str(counter)] = action
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

    def __init__(self, input_settings: InputSettings, output_settings: OutputSettings, credentials: CICredentials):
        super().__init__(input_settings=input_settings, output_settings=output_settings)
        self.client = BambooClient(credentials=credentials)

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
        actions: dict[Any, Action] = extract_actions(stages=specs.stages)
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
