# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes
from typing import Optional, Any, List


# This file contains a simplified view of the Bamboo Specs, as returned by the Bamboo REST API.
# We only use the fields that help us in crafting a working Aeolus spec file.


class BambooPlan:
    """
    BambooPlan represents a Bamboo plan as returned by the Bamboo REST API.
    """

    def __init__(self, project_key: str, key: str, name: str, description: str) -> None:
        self.project_key = project_key
        self.key = key
        self.name = name
        self.description = description

    project_key: str
    key: str
    name: str
    description: str


class BambooCheckoutTask:
    """
    BambooCheckoutTask represents a Bamboo checkout task as returned by the Bamboo REST API.
    """

    def __init__(
        self, repository: str, force_clean_build: bool, path: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        self.repository = repository
        self.force_clean_build = force_clean_build
        self.path = path if path is not None else "."
        self.description = description

    repository: str
    path: str
    force_clean_build: bool
    description: Optional[str]


class BambooConditionVariable:
    """
    BambooConditionVariable represents a Bamboo condition variable as returned by the Bamboo REST API.
    """

    def __init__(self, matches: dict[str, str]) -> None:
        self.matches = matches

    matches: dict[str, str]


class BambooCondition:
    """
    BambooCondition represents a Bamboo condition as returned by the Bamboo REST API.
    """

    def __init__(self, variables: list[BambooConditionVariable]) -> None:
        self.variables = variables

    variables: list[BambooConditionVariable]


class BambooTask:
    """
    BambooTask represents a Bamboo task as returned by the Bamboo REST API.
    """

    def __init__(
        self,
        interpreter: Optional[str],
        scripts: List[str],
        environment: dict[Any, int | str | float | bool | list | None],
        description: str,
        condition: Optional[BambooCondition],
        arguments: Optional[list[str]] = None,
        always_execute: bool = False,
    ) -> None:
        if arguments is None:
            arguments = []
        self.interpreter = interpreter
        self.scripts = scripts
        self.environment = environment
        self.description = description
        self.condition = condition
        self.arguments = arguments
        self.always_execute = always_execute

    interpreter: Optional[str]
    scripts: list[str]
    environment: dict[Any, int | str | float | bool | list | None]
    description: str
    condition: Optional[BambooCondition]
    arguments: list[str]
    always_execute: bool


class BambooSpecialTask(BambooTask):
    """
    SpecialBambooTask represents a special Bamboo task as returned by the Bamboo REST API.
    """

    def __init__(
        self,
        executable: Optional[str],
        jdk: Optional[str],
        goal: Optional[str],
        tests: Optional[str],
        interpreter: Optional[str],
        scripts: list[str],
        parameters: dict[Any, int | str | float | bool | list | None],
        environment: dict[Any, int | str | float | bool | list | None],
        description: str,
        condition: Optional[BambooCondition],
        always_execute: bool,
        task_type: str,
    ) -> None:
        super().__init__(
            interpreter=interpreter,
            scripts=scripts,
            environment=environment,
            description=description,
            condition=condition,
            always_execute=always_execute,
        )
        self.task_type = task_type
        self.parameters = parameters
        self.executable = executable
        self.jdk = jdk
        self.goal = goal
        self.tests = tests

    executable: Optional[str]
    jdk: Optional[str]
    goal: Optional[str]
    tests: Optional[str]
    parameters: dict[Any, int | str | float | bool | list | None]
    task_type: str


class BambooDockerConfig:
    """
    BambooDockerConfig represents the docker configuration of a Bamboo job as returned by the Bamboo REST API.
    """

    def __init__(self, image: str, volumes: dict[str, str], docker_run_arguments: list[str]) -> None:
        self.image = image
        self.volumes = volumes
        self.docker_run_arguments = docker_run_arguments

    image: str
    volumes: dict[str, str]
    docker_run_arguments: list[str]


class BambooJob:
    """
    BambooJob represents a Bamboo job as returned by the Bamboo REST API.
    """

    def __init__(
        self,
        key: str,
        tasks: list[BambooCheckoutTask | BambooTask | BambooSpecialTask],
        artifact_subscriptions: list[Any],
        docker: Optional[BambooDockerConfig],
        other: Optional[dict[str, Any]],
    ) -> None:
        self.key = key
        self.tasks = tasks
        self.artifact_subscriptions = artifact_subscriptions
        self.docker = docker
        self.other = other

    key: str
    tasks: list[BambooCheckoutTask | BambooTask]
    artifact_subscriptions: list[Any]
    docker: Optional[BambooDockerConfig]
    other: Optional[dict[str, Any]]


class BambooStage:
    """
    BambooStage represents a Bamboo stage as returned by the Bamboo REST API.
    """

    def __init__(self, manual: bool, final: bool, jobs: dict[str, BambooJob]) -> None:
        self.manual = manual
        self.final = final
        self.jobs = jobs

    manual: bool
    final: bool
    jobs: dict[str, BambooJob]


class BambooRepository:
    """
    BambooRepository represents a Bamboo repository as returned by the Bamboo REST API.
    """

    def __init__(
        self,
        repo_type: str,
        url: str,
        branch: str,
        shared_credentials: str,
        command_timeout_minutes: str,
        lfs: bool,
        verbose_logs: bool,
        use_shallow_clones: bool,
        cache_on_agents: bool,
        submodules: bool,
        ssh_key_applies_to_submodules: bool,
        fetch_all: bool,
    ) -> None:
        self.repo_type = repo_type
        self.url = url
        self.branch = branch
        self.shared_credentials = shared_credentials
        self.command_timeout_minutes = command_timeout_minutes
        self.lfs = lfs
        self.verbose_logs = verbose_logs
        self.use_shallow_clones = use_shallow_clones
        self.cache_on_agents = cache_on_agents
        self.submodules = submodules
        self.ssh_key_applies_to_submodules = ssh_key_applies_to_submodules
        self.fetch_all = fetch_all

    repo_type: str
    url: str
    branch: str
    shared_credentials: str
    command_timout_minutes: str
    lfs: bool
    verbose_logs: bool
    use_shallow_clones: bool
    cache_on_agents: bool
    submodules: bool
    ssh_key_applies_to_submodules: bool
    fetch_all: bool


class BambooSpecs:
    """
    BambooSpecs represents the specs of a Bamboo plan as returned by the Bamboo REST API.
    """

    def __init__(
        self,
        version: int,
        plan: BambooPlan,
        stages: dict[str, BambooStage],
        variables: dict[str, str],
        triggers: list[Any],
        repositories: dict[str, BambooRepository],
    ) -> None:
        super().__init__()
        self.version = version
        self.plan = plan
        self.stages = stages
        self.variables = variables
        self.triggers = triggers
        self.repositories = repositories

    version: int
    plan: BambooPlan
    stages: dict[str, BambooStage]
    variables: dict[str, str]
    triggers: list[Any]
    repositories: dict[str, BambooRepository]
