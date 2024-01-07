import json
import os
import time
import warnings
from typing import Optional, Dict, Any

import yaml
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.status import HTTP_401_UNAUTHORIZED

import _paths  # pylint: disable=unused-import # noqa: F401
from api_classes.publish_payload import PublishPayload
from api_classes.result_format import ResultFormat
from api_classes.translate_payload import TranslatePayload
from api_utils import utils

# pylint: disable=wrong-import-order
from api_utils.utils import dump_yaml
from classes.ci_credentials import CICredentials
from classes.generated.definitions import Target
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.output_settings import OutputSettings
from classes.pass_metadata import PassMetadata
from classes.translator import BambooTranslator
from classes.validator import Validator
from classes.yaml_dumper import YamlDumper
from cli_utils import logger
from cli_utils.utils import TemporaryFileWithContent
from generators.bamboo import BambooGenerator
from generators.cli import CliGenerator
from generators.jenkins import JenkinsGenerator

app = FastAPI()

origins = ["http://localhost", "http://localhost:3000", "https://aeolus.resch.io", "http://localhost:9000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Any) -> Any:
    """
    Adds the process time to the response header.
    :param request: the request
    :param call_next: next middleware
    :return: the response
    """
    start_time: float = time.time()
    response: Any = await call_next(request)
    process_time: float = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def check_token(request: Request, call_next: Any) -> Any:
    """
    Checks the token of the request.
    :param request: the request
    :param response: the response
    :param call_next: next middleware
    :return: the response
    """
    if is_authorized(request=request):
        return await call_next(request)
    return PlainTextResponse("Unauthorized", status_code=HTTP_401_UNAUTHORIZED)


def needs_auth() -> bool:
    """
    Checks whether the api needs authentication.
    :return: True if authentication is needed, otherwise False
    """
    tokens: Optional[str] = os.getenv("AEOLUS_API_KEYS")
    return tokens is not None


def is_authorized(request: Request) -> bool:
    """
    Checks the token of the request.
    :param request: the request
    :return: the response
    """
    tokens: Optional[str] = os.getenv("AEOLUS_API_KEYS")
    if not tokens:
        return True
    if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json"):
        return True
    token_list = tokens.split(",")
    if request.headers.get("Authorization") in [f"Bearer {token}" for token in token_list]:
        return True

    return False


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """
    Health check endpoint.
    :return: ok if everything is fine
    """
    return {"status": "ok"}


@app.post("/validate")
async def validate(windfile: WindFile) -> WindFile | dict[str, str] | None:
    """
    Validates the given windfile.
    :param windfile: Windfile to validate
    :return: Windfile if valid, otherwise a dict with the error message, which can look like this
    {
      "detail": [
        {
          "type": "missing",
          "loc": [
            "body",
            "actions"
          ],
          "msg": "Field required",
          "input": {
            "api": "v0.0.1",
            "metadata": {
              "name": "name",
              "id": null,
              "description": "description",
              "author": "test",
              "targets": null,
              "gitCredentials": null,
              "docker": null
            },
            "environment": null,
            "repositories": null
          },
          "url": "https://errors.pydantic.dev/2.1/v/missing"
        }
      ]
    }
    """
    with TemporaryFileWithContent(content=dump_yaml(content=windfile)) as file:
        input_settings: InputSettings = InputSettings(file=file, file_path=file.name)
        output_settings: OutputSettings = OutputSettings(verbose=True, debug=True, emoji=True)
        validator: Validator = Validator(output_settings=output_settings, input_settings=input_settings)
        return validator.validate_wind_file()


@app.post("/generate/{target}/yaml")
async def generate_from_yaml(request: Request, target: Target) -> Optional[Dict[str, str | None]]:
    """
    Generates the given windfile for the given target directly from yaml. It's advised to use
    the json endpoint, as it is fully supported and does not require manual parsing of the body like
    in this endpoint. The functionality of this endpoint is the same as the json endpoint.
    :param request: Request that contains a valid yaml windfile
    :param target: Target to generate for (cli, jenkins, bamboo)
    :return: Generated script
    """
    raw_body = await request.body()
    try:
        data: WindFile = WindFile(**yaml.safe_load(raw_body))
        return generate_target_script(windfile=data, target=target)
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=422, detail="Invalid YAML") from exc


def generate_target_script(
    windfile: WindFile, target: Target, credentials: Optional[CICredentials] = None
) -> Optional[Dict[str, str | None]]:
    """
    Generates the given windfile for the given target.
    :param credentials: Credentials to use for publishing
    :param windfile: Windfile to generate
    :param target: Target to generate for
    :return:
    """
    with TemporaryFileWithContent(content=dump_yaml(content=windfile)) as file:
        input_settings: InputSettings = InputSettings(file=file, file_path=file.name, target=target)
        output_settings: OutputSettings = OutputSettings(verbose=True, debug=True, emoji=True)
        output_settings.ci_credentials = credentials
        metadata: PassMetadata = PassMetadata()
        merger: Merger = Merger(
            windfile=windfile, input_settings=input_settings, output_settings=output_settings, metadata=metadata
        )
        start: float = time.time()
        merged: Optional[WindFile] = merger.merge()
        end: float = time.time()
        logger.info("⏰", f"Merged windfile in {end - start}", output_settings.emoji)
        if not merged:
            return None
        generator: Optional[CliGenerator | JenkinsGenerator | BambooGenerator] = None
        if target == Target.cli:
            generator = CliGenerator(
                input_settings=input_settings,
                output_settings=output_settings,
                windfile=merged,
                metadata=merger.metadata,
            )
        if target == Target.bamboo:
            generator = BambooGenerator(
                input_settings=input_settings,
                output_settings=output_settings,
                windfile=merged,
                metadata=merger.metadata,
            )
        if target == Target.jenkins:
            generator = JenkinsGenerator(
                input_settings=input_settings,
                output_settings=output_settings,
                windfile=merged,
                metadata=merger.metadata,
            )
        if generator:
            return {"result": generator.generate(), "key": generator.key}
        return {"detail": "Unknown target"}


@app.post("/generate/{target}")
async def generate(windfile: WindFile, target: Target) -> Optional[Dict[str, str | None]]:
    """
    Generates the given windfile for the given target.
    :param windfile: Windfile to generate
    :param target: Target to generate for
    :return:
    """
    return generate_target_script(windfile=windfile, target=target)


@app.post("/publish/{target}")
def publish(payload: PublishPayload, target: Target) -> Dict[str, Optional[str]]:
    """
    Publishes the given windfile for the given target using the provided credentials.
    :param payload: Payload with credentials and windfile
    :param target: Target to publish for
    """
    windfile: Optional[WindFile] = None
    if needs_auth():
        if target == Target.cli:
            raise HTTPException(status_code=422, detail="CLI does not support publishing")
        if target == Target.bamboo:
            payload.url = payload.url or os.getenv("BAMBOO_URL")
            payload.username = payload.username or os.getenv("BAMBOO_USERNAME")
            payload.token = payload.token or os.getenv("BAMBOO_TOKEN")
        elif target == Target.jenkins:
            payload.url = payload.url or os.getenv("JENKINS_URL")
            payload.username = payload.username or os.getenv("JENKINS_USERNAME")
            payload.token = payload.token or os.getenv("JENKINS_TOKEN")
    try:
        windfile = WindFile(**yaml.safe_load(payload.windfile))
    except yaml.YAMLError:
        pass
    if not windfile:
        try:
            windfile = json.loads(payload.windfile)
        except ValueError:
            pass
    if not windfile:
        raise HTTPException(status_code=422, detail="Invalid windfile")
    if payload.url and payload.username and payload.token:
        generated: Optional[Dict[str, str | None]] = generate_target_script(
            windfile=windfile,
            target=target,
            credentials=CICredentials(url=payload.url, username=payload.username, token=payload.token),
        )
        if not generated:
            return {"detail": "generation failed, check api logs"}
        return generated
    return {"detail": "missing credentials"}


@app.put("/translate/{source}/{build_plan_id}")
def translate(
    payload: TranslatePayload,
    source: Target,
    build_plan_id: str,
    result_format: ResultFormat = ResultFormat.JSON,
    exclude_repositories: bool = False,
) -> Optional[WindFile | str]:
    """
    Translates the build plan id to a target.
    :param payload: Payload with credentials
    :param source: Source target, currently only bamboo is supported
    :param build_plan_id: Build plan id to translate
    :param result_format: Format to return the windfile in
    :param exclude_repositories: Whether to exclude the repositories from the windfile or not
    :return: Windfile with the translated target
    """
    if needs_auth():
        if source == Target.bamboo:
            payload.url = os.getenv("BAMBOO_URL", "needs to be set")
            payload.username = os.getenv("BAMBOO_USERNAME", "needs to be set")
            payload.token = os.getenv("BAMBOO_TOKEN", "needs to be set")
    if source != Target.bamboo:
        raise HTTPException(status_code=422, detail="Invalid source target")
    output_settings: OutputSettings = OutputSettings(verbose=True, debug=True, emoji=True)
    ci_credentials: CICredentials = CICredentials(url=payload.url, username=payload.username, token=payload.token)
    input_settings: InputSettings = InputSettings(file_path="none", target=Target.bamboo, file=None)
    translator: BambooTranslator = BambooTranslator(
        input_settings=input_settings, output_settings=output_settings, credentials=ci_credentials
    )
    try:
        windfile: Optional[WindFile] = translator.translate(plan_key=build_plan_id)
        if exclude_repositories and windfile:
            windfile.repositories = None
        if result_format == ResultFormat.JSON:
            if windfile:
                warnings.filterwarnings("ignore", category=UserWarning)
                utils.remove_none_values(windfile)
                utils.remove_none_values(windfile.metadata)
                for action in windfile.actions:  # pylint: disable=not-an-iterable
                    utils.remove_none_values(action.root)
                return windfile
        elif windfile:
            json_repr: str = windfile.model_dump_json(exclude_none=True)
            return yaml.dump(yaml.safe_load(json_repr), sort_keys=False, Dumper=YamlDumper, default_flow_style=False)
    except Exception as exc:
        logger.error("🚨", f"Failed to translate {build_plan_id}", output_settings.emoji)
        logger.error("🚨", f"{exc}", output_settings.emoji)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return None
