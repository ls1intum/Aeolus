from typing import Optional, Tuple, Any
import re
import yaml

from classes.bamboo_specs import BambooSpecs, BambooPlan, BambooJob, BambooStage, BambooCheckoutTask, BambooTask
from classes.bamboo_client import BambooClient
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
)
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.pass_settings import PassSettings
from utils import logger


class BambooTranslator(PassSettings):
    source: Target = Target.bamboo
    client: BambooClient

    def __init__(
        self,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        url: str,
        token: str,
        target: Target = Target.bamboo,
    ):
        super().__init__(input_settings=input_settings, output_settings=output_settings)
        if target != Target.bamboo:
            print("BambooTranslator only supports Bamboo as target")
            exit(1)
        self.client = BambooClient(url=url, token=token)
        self.target = target

    def combine_docker_config(self, windfile: WindFile):
        docker_configs: dict[str, Optional[Docker]] = {}
        for action in windfile.actions:
            docker_configs[action] = windfile.actions[action].root.docker
        first: Optional[Docker] = list(docker_configs.values())[0]
        are_identical: bool = True
        for docker_config in docker_configs:
            if first != docker_configs[docker_config]:
                logger.info("🚧", "Docker configurations are not identical", self.output_settings.emoji)
                are_identical = False
                break
        if are_identical:
            logger.info("🚀", "Docker configurations are identical", self.output_settings.emoji)
            windfile.metadata.docker = first
            for action in windfile.actions:
                windfile.actions[action].root.docker = None

    def clean_up(self, windfile: WindFile) -> None:
        for action in windfile.actions:
            root_action: FileAction | InternalAction | PlatformAction | ExternalAction = windfile.actions[action].root
            if (
                root_action.environment is not None
                and len(root_action.environment.root.root) == 0
            ):
                root_action.environment = None
            if (
                root_action.parameters is not None
                and len(root_action.parameters.root.root) == 0
            ):
                root_action.parameters = None
            if (
                root_action.excludeDuring is not None
                and len(root_action.excludeDuring) == 0
            ):
                root_action.excludeDuring = None

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
        actions: dict[Any, Action] = {}
        repositories: dict[str, Repository] = {}
        for stage_name in specs.stages:
            stage: BambooStage = specs.stages[stage_name]
            for job_name in stage.jobs:
                job: BambooJob = stage.jobs[job_name]
                counter: int = 0
                for task in job.tasks:
                    if isinstance(task, BambooCheckoutTask):
                        checkout: BambooCheckoutTask = task
                        repository: Repository = Repository(
                            url=specs.repositories[checkout.repository].url,
                            branch=specs.repositories[checkout.repository].branch,
                            path=checkout.path,
                        )
                        repositories[checkout.repository] = repository
                    elif isinstance(task, BambooTask):
                        exclude: list[Lifecycle] = []
                        if task.condition is not None:
                            for condition in task.condition.variables:
                                for match in condition.matches:
                                    regex = re.compile("[^a-zA-Z\ \|\_]")
                                    lifecycle = condition.matches[match]
                                    for entry in regex.sub("", lifecycle).split("|"):
                                        exclude.append(Lifecycle[entry])
                        scriptTask: BambooTask = task
                        docker: Optional[Docker] = None
                        if job.docker is not None:
                            volume_list: list[str] = []
                            for volume in job.docker.volumes:
                                volume_list.append(f"{volume}:{job.docker.volumes[volume]}")
                            docker = Docker(
                                image=job.docker.image
                                if ":" not in job.docker.image
                                else job.docker.image.split(":")[0],
                                tag=job.docker.image.split(":")[1] if ":" in job.docker.image else "latest",
                                volumes=volume_list,
                                parameters=job.docker.docker_run_arguments,
                            )
                        environment: Environment = Environment(root=Dictionary(root=scriptTask.environment))
                        action: Action = Action(root=InternalAction(
                            script="\n".join(scriptTask.scripts),
                            excludeDuring=exclude,
                            docker=docker,
                            environment=environment,
                            platform=None,
                        ))
                        counter += 1
                        actions[job.key + str(counter)] = action
        metadata: WindfileMetadata = WindfileMetadata(
            name=plan.name,
            description=plan.description,
            author=Author(root="bamboo"),
            docker=None,
            targets=None,
            gitCredentials=specs.repositories[list(specs.repositories.keys())[0]].shared_credentials,
        )
        windfile: WindFile = WindFile(
            api=Api(root="v0.0.1"), metadata=metadata, actions=actions, repositories=repositories
        )
        self.combine_docker_config(windfile=windfile)
        self.clean_up(windfile=windfile)
        # work-around as enums do not get cleanly printed with model_dump
        json: str = windfile.model_dump_json(exclude_none=True)
        logger.info("🪄", "Translated windfile", self.output_settings.emoji)
        print(yaml.dump(yaml.safe_load(json), sort_keys=False))
        return None
