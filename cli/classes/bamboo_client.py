from typing import Optional, Tuple, Any
from xml.dom.minidom import parseString, Document, Node

import requests
import yaml

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
)


class BambooClient:
    url: str = ""
    token: str = ""

    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token

    def handle_tasks(self, job_dict: list[dict[str, Any]]) -> list[BambooTask | BambooCheckoutTask]:
        tasks: list[BambooTask | BambooCheckoutTask] = []
        for task in job_dict:
            task = self.fix_keys(dictionary=task)
            task_type: str = list(task.keys())[0]
            task_dict: dict[str, Optional[int | bool | str | dict[str, Any] | list[str]]] = self.fix_keys(
                dictionary=task[task_type]
            )
            if task_type == "script":
                condition: Optional[BambooCondition] = None
                environment: dict[Any, str | float | None] = {}
                if "environment" in task_dict:
                    for entry in str(task_dict["environment"]).split(";"):
                        key, value = entry.split("=")
                        environment[key] = value
                if "conditions" in task_dict and isinstance(task_dict["conditions"], list):
                    for entry in task_dict["conditions"]:
                        # TODO check if this behaves differently if there are more than one conditions
                        dictionary: dict[str, dict[str, str]] = self.fix_keys(dictionary=entry)
                        matches: dict[str, dict[str, str]] = self.fix_keys(dictionary=dictionary["variable"])
                        variable: BambooConditionVariable = BambooConditionVariable(matches=matches["matches"])
                        if condition is None:
                            condition = BambooCondition(variables=[variable])
                        else:
                            condition.variables.append(variable)
                scripts: list[str] = []
                if "scripts" in task_dict:
                    for script in task_dict["scripts"]:
                        scripts.append(str(script))
                task = BambooTask(
                    interpreter=str(task_dict["interpreter"]),
                    scripts=scripts,
                    environment=environment,
                    description=str(task_dict["description"]) if "description" in task_dict else "",
                    condition=condition,
                )
                tasks.append(task)
            elif task_type == "checkout":
                checkout: BambooCheckoutTask = BambooCheckoutTask(**task_dict)
                tasks.append(checkout)
            else:
                print(f"Task type {task_type} is not implemented")
                # raise NotImplementedError(f"Task type {task_type} is not implemented")
        return tasks

    def handle_final_tasks(
        self,
        final_tasks: list[dict[str, Any]],
    ):
        # TODO think about final tasks management in aeolus
        # for now, add them at the end
        tmp: list[dict[str, Any]] = final_tasks
        tasks: list[dict[str, Any]] = []
        for item in tmp:
            old_key: str = list(item.keys())[0]
            task_type: str = item[old_key]["type"] if "type" in item[old_key] else old_key
            if "type" in item[old_key]:
                del item[old_key]["type"]
            tasks.append({task_type: item[old_key]})
        return tasks

    def convert_stages(self, plan_specs: dict[str, Any]) -> dict[str, BambooStage]:
        stages: dict[str, BambooStage] = {}
        dictionary: list[dict[str, Any]] = plan_specs["stages"]

        for stage_dict in dictionary:
            stage_name = list(stage_dict.keys())[0]
            job_list: list[str] = stage_dict[stage_name]["jobs"]
            stage_dict[stage_name]["jobs"] = {}
            stage: BambooStage = BambooStage(**stage_dict[stage_name])
            for job_name in job_list:
                job_dict: dict[str, Optional[int | bool | str | dict[str, Any] | list[Any]]] = plan_specs[job_name]
                job_dict = self.fix_keys(dictionary=job_dict)
                if "docker" in job_dict:
                    # we handle docker "tasks" differently (in the metadata rather then a job), so we remove them here
                    # to make the creation of the BambooSpecs object easier
                    docker_config: dict[str, Any] = self.fix_keys(job_dict["docker"])
                    job_dict["docker"] = BambooDockerConfig(**docker_config)
                else:
                    job_dict["docker"] = None
                if "final_tasks" in job_dict:
                    for final in self.handle_final_tasks(final_tasks=job_dict["final_tasks"]):
                        job_dict["tasks"].append(final)
                    del job_dict["final_tasks"]
                if "other" not in job_dict:
                    job_dict["other"] = None
                job: BambooJob = BambooJob(**job_dict)
                tasks: list[BambooTask] = self.handle_tasks(job_dict=job_dict["tasks"])
                job.tasks = tasks
                stage.jobs[job_name] = job
            stages[stage_name] = stage
        return stages

    def get_plan_yaml(self, plan_key: str) -> Optional[Tuple[BambooSpecs, dict[str, str]]]:
        """
        Get the YAML representation of the given plan by using the REST API.
        :param plan_key:
        :return: YAML representation of the plan
        """
        auth: dict = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.url}/rest/api/latest/plan/{plan_key}/specs?all", params={"format": "yaml"}, headers=auth
        )
        if response.status_code != 200:
            return None
        document: Document = parseString(response.text)
        code_node: Node | None = document.firstChild.firstChild.firstChild
        if code_node is not None and code_node.firstChild is not None:
            code: str = code_node.firstChild.nodeValue

            specs: str = code.split("\n---\n")[0]
            # permissions: str = code.split("\n---\n")[1]
            dictionary: dict[str, Any] = yaml.safe_load(specs)
            dictionary["plan"] = self.fix_keys(dictionary=dictionary["plan"])
            stages: dict[str, BambooStage] = self.convert_stages(plan_specs=dictionary)
            repositories: dict[str, BambooRepository] = {}
            for repo_dict in dictionary["repositories"]:
                repo_name = list(repo_dict.keys())[0]
                repo: dict[str, int | bool | str] = repo_dict[repo_name]
                repo = self.fix_keys(dictionary=repo)
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

    def fix_keys(self, dictionary: dict[str, Any]) -> dict[str, Any]:
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
