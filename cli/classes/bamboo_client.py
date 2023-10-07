from typing import Optional, Tuple, Any
from xml.dom.minidom import parseString, Document, Text, Node

import requests
import yaml

from classes.bamboo_credentials import BambooCredentials
from classes.bamboo_specs import (
    BambooSpecs,
    BambooPlan,
    BambooStage,
    BambooRepository,
    BambooJob,
    BambooTask,
    BambooCheckoutTask,
    BambooCondition,
    BambooConditionVariable,
    BambooDockerConfig,
    BambooSpecialTask,
)


def handle_final_tasks(
    final_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Handle final tasks in the Bamboo response. We iterate over
    the list of final tasks and prepare them to be added
    to the list of tasks. Also, we set always_execute to True
    :param final_tasks: list of final tasks from Bamboo
    :return: list of final tasks that can be added to the list of tasks
    """
    # think about final tasks management in aeolus
    # for now, add them at the end, and always execute them
    tmp: list[dict[str, Any]] = final_tasks
    tasks: list[dict[str, Any]] = []
    for item in tmp:
        old_key: str = list(item.keys())[0]
        task_type: str = item[old_key]["type"] if "type" in item[old_key] else old_key
        if "type" in item[old_key]:
            del item[old_key]["type"]
        item[old_key]["always_execute"] = True
        tasks.append({task_type: item[old_key]})
    return tasks


def fix_keys(dictionary: dict[str, Any]) -> dict[str, Any]:
    """
    Replace all "-" in keys with "_"
    :param dictionary to fix
    :return: dictionary with fixed keys
    """
    clean: dict[str, Any] = {}
    for key in dictionary.keys():
        if "-" in key:
            clean[key.replace("-", "_")] = dictionary[key]
        else:
            clean[key] = dictionary[key]
    return clean


class BambooClient:
    """
    Client for the Bamboo REST API.
    """

    credentials: BambooCredentials

    def __init__(self, credentials: BambooCredentials):
        self.credentials = credentials

    def parse_condition(self, conditions: Optional[list[str] | list[dict[str, Any]]]) -> Optional[BambooCondition]:
        """
        Parse a condition string into a BambooCondition object.
        :param conditions: conditions from Bamboo Response
        :return: BambooCondition object
        """
        if conditions is None:
            return None
        condition: Optional[BambooCondition] = None
        for entry in conditions:
            # check if this behaves differently if there are more than one conditions
            if isinstance(entry, dict):
                dictionary: dict[str, dict[str, str]] = fix_keys(dictionary=entry)
                matches: dict[str, dict[str, str]] = fix_keys(dictionary=dictionary["variable"])
                variable: BambooConditionVariable = BambooConditionVariable(matches=matches["matches"])
                if condition is None:
                    condition = BambooCondition(variables=[variable])
                else:
                    condition.variables.append(variable)
        return condition

    def handle_script_task(self, task_dict: dict[str, Any]) -> BambooTask:
        condition: Optional[BambooCondition] = None
        conditions: Optional[int | bool | str | dict[str, Any] | list[str]] | list[dict[str, Any]] = task_dict.get(
            "conditions", None
        )
        if isinstance(conditions, list) and len(conditions) > 0 and isinstance(conditions[0], dict):
            condition = self.parse_condition(conditions=conditions)
        environment: dict[Any, str | float | None] = {}
        if "environment" in task_dict:
            for entry in str(task_dict["environment"]).split(";"):
                key, value = entry.split("=")
                environment[key] = value
        scripts: list[str] = []
        if "scripts" in task_dict and isinstance(task_dict["scripts"], list):
            for script in task_dict["scripts"]:
                scripts.append(str(script))
        return BambooTask(
            interpreter=str(task_dict["interpreter"]),
            scripts=scripts,
            environment=environment,
            description=str(task_dict["description"]) if "description" in task_dict else "",
            condition=condition,
            always_execute=bool(task_dict["always_execute"]) if "always_execute" in task_dict else False,
        )

    def handle_tasks(self, job_dict: list[dict[str, Any]]) -> list[BambooTask | BambooCheckoutTask | BambooSpecialTask]:
        """
        Handle the tasks in the Bamboo response. We iterate over the job
        and convert the tasks into easy to work with objects.
        :param job_dict: list of jobs from Bamboo
        :return: list of BambooTask objects
        """
        tasks: list[BambooTask | BambooCheckoutTask | BambooSpecialTask] = []
        for task in job_dict:
            task = fix_keys(dictionary=task)
            task_type: str = list(task.keys())[0]
            task_dict: dict[
                str, Optional[int | bool | str | dict[str, Any] | list[str]] | list[dict[str, Any]]
            ] = fix_keys(dictionary=task[task_type])
            if task_type == "junit":
                parameters: dict[Any, int | bool | str | float | None] = {}
                for key, value in task_dict.items():
                    if key not in ["type", "description", "always_execute"]:
                        if isinstance(value, (str, int, bool, float)):
                            parameters[key] = value
                tasks.append(
                    BambooSpecialTask(
                        interpreter=task_type,
                        scripts=[],
                        parameters=parameters,
                        environment={},
                        description=str(task_dict["description"]) if "description" in task_dict else "",
                        condition=None,
                        always_execute=bool(task_dict["always_execute"]) if "always_execute" in task_dict else False,
                        task_type=str(task_type),
                    )
                )
            elif task_type == "script":
                tasks.append(self.handle_script_task(task_dict=task_dict))
            elif task_type == "checkout":
                tasks.append(
                    BambooCheckoutTask(
                        repository=str(task_dict["repository"]),
                        force_clean_build=bool(task_dict["force_clean_build"]),
                        path=str(task_dict["path"]) if "path" in task_dict else "",
                        description=str(task_dict["description"]) if "description" in task_dict else "",
                    )
                )
            else:
                print(f"Task type {task_type} is not implemented")
                # raise NotImplementedError(f"Task type {task_type} is not implemented")
        return tasks

    def convert_stages(self, plan_specs: dict[str, Any]) -> dict[str, BambooStage]:
        """
        We convert the stages from the API response into structured
        objects that are easier to work with.
        :param plan_specs: Response from the Bamboo API
        :return: dict of BambooStage objects including BambooJob and BambooTask objects
        """
        stages: dict[str, BambooStage] = {}
        dictionary: list[dict[str, Any]] = plan_specs["stages"]

        for stage_dict in dictionary:
            stage_name = list(stage_dict.keys())[0]
            job_list: list[str] = stage_dict[stage_name]["jobs"]
            stage_dict[stage_name]["jobs"] = {}
            bamboo_docker: Optional[BambooDockerConfig] = None
            stage: BambooStage = BambooStage(**stage_dict[stage_name])
            for job_name in job_list:
                job_dict: dict[str, Optional[int | bool | str | dict[str, Any] | list[Any]]] = plan_specs[job_name]
                job_dict = fix_keys(dictionary=job_dict)
                if "docker" in job_dict and isinstance(job_dict["docker"], dict):
                    # we handle docker "tasks" differently (in the metadata rather than a job), so we remove them here
                    # to make the creation of the BambooSpecs object easier
                    bamboo_docker = BambooDockerConfig(
                        image=str(job_dict["docker"]["image"]),
                        volumes=job_dict["docker"]["volumes"]
                        if isinstance(job_dict["docker"]["volumes"], dict)
                        else {},
                        docker_run_arguments=job_dict["docker"]["docker-run-arguments"]
                        if isinstance(job_dict["docker"]["docker-run-arguments"], list)
                        else [],
                    )
                if (
                    "final_tasks" in job_dict
                    and isinstance(job_dict["final_tasks"], list)
                    and isinstance(job_dict["tasks"], list)
                ):
                    for final in handle_final_tasks(final_tasks=job_dict["final_tasks"]):
                        job_dict["tasks"].append(final)
                    del job_dict["final_tasks"]
                if "other" not in job_dict:
                    job_dict["other"] = None
                tasks_dict: Optional[list[dict[str, Any]]] = None
                if (
                    isinstance(job_dict["tasks"], list)
                    and len(job_dict["tasks"]) > 0
                    and isinstance(job_dict["tasks"][0], dict)
                ):
                    tasks_dict = job_dict["tasks"]
                if tasks_dict is None:
                    continue
                tasks: list[BambooCheckoutTask | BambooTask | BambooSpecialTask] = self.handle_tasks(
                    job_dict=tasks_dict
                )
                job: BambooJob = BambooJob(
                    key=str(job_dict["key"]),
                    tasks=tasks,
                    artifact_subscriptions=job_dict["artifact_subscriptions"]
                    if isinstance(job_dict["artifact_subscriptions"], list)
                    else [],
                    docker=bamboo_docker,
                    other=job_dict["other"] if isinstance(job_dict["other"], dict) else None,
                )
                stage.jobs[job_name] = job
            stages[stage_name] = stage
        return stages

    def extract_code(self, node: Node) -> Optional[str]:
        """
        Extract the YAML code for a plan from the given xml document.
        :param node: xml node
        :return: YAML code
        """
        if node.firstChild is None:
            if isinstance(node, Text):
                element: Text = node
                return element.data
            return None
        return self.extract_code(node=node.firstChild)

    def get_plan_yaml(self, plan_key: str) -> Optional[Tuple[BambooSpecs, dict[str, str]]]:
        """
        Get the YAML representation of the given plan by using the REST API.
        :param plan_key:
        :return: YAML representation of the plan
        """
        response = requests.get(
            f"{self.credentials.url}/rest/api/latest/plan/{plan_key}/specs?all",
            params={"format": "yaml"},
            headers={"Authorization": f"Bearer {self.credentials.token}"},
            timeout=30,
        )
        if response.status_code != 200:
            return None
        document: Document = parseString(response.text)
        code: Optional[str] = self.extract_code(node=document)
        if code is not None:
            specs: str = code.split("\n---\n")[0]
            # permissions: str = code.split("\n---\n")[1]
            dictionary: dict[str, Any] = yaml.safe_load(specs)
            dictionary["plan"] = fix_keys(dictionary=dictionary["plan"])
            stages: dict[str, BambooStage] = self.convert_stages(plan_specs=dictionary)
            repositories: dict[str, BambooRepository] = {}
            for repo_dict in dictionary["repositories"]:
                repo_name = list(repo_dict.keys())[0]
                repo: dict[str, int | bool | str] = repo_dict[repo_name]
                repo = fix_keys(dictionary=repo)
                repositories[repo_name] = BambooRepository(
                    repo_type=str(repo["type"]),
                    url=str(repo["url"]),
                    branch=str(repo["branch"]),
                    shared_credentials=str(repo["shared_credentials"]),
                    command_timeout_minutes=str(repo["command_timeout_minutes"]),
                    lfs=bool(repo["lfs"]),
                    verbose_logs=bool(repo["verbose_logs"]),
                    use_shallow_clones=bool(repo["use_shallow_clones"]),
                    cache_on_agents=bool(repo["cache_on_agents"]),
                    submodules=bool(repo["submodules"]),
                    ssh_key_applies_to_submodules=bool(repo["ssh_key_applies_to_submodules"]),
                    fetch_all=bool(repo["fetch_all"]),
                )
            sanitized: dict = {
                "version": dictionary["version"],
                "plan": BambooPlan(**dictionary["plan"]),
                "stages": stages,
                "variables": dictionary["variables"] if "variables" in dictionary else {},
                "triggers": dictionary["triggers"],
                "repositories": repositories,
            }
            bamboo_specs: BambooSpecs = BambooSpecs(**sanitized)
            return bamboo_specs, yaml.safe_load(specs)
        return None
