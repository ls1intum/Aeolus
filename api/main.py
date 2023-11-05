import json
import time
from typing import Optional, Dict, Any

import yaml
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

import _paths  # pylint: disable=unused-import # noqa: F401
from api_classes.publish_payload import PublishPayload
# pylint: disable=wrong-import-order
from api_utils.utils import dump_yaml
from classes.ci_credentials import CICredentials
from classes.generated.definitions import Target
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.output_settings import OutputSettings
from classes.pass_metadata import PassMetadata
from classes.validator import Validator
from cli_utils import logger
from cli_utils.utils import TemporaryFileWithContent
from generators.bamboo import BambooGenerator
from generators.cli import CliGenerator
from generators.jenkins import JenkinsGenerator

app = FastAPI()

origins = ["http://localhost", "http://localhost:3000", "https://aeolus.resch.io"]

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
async def generate_from_yaml(request: Request, target: Target) -> Optional[Dict[str, str]]:
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
async def generate(windfile: WindFile, target: Target) -> Optional[Dict[str, str]]:
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
    generated: Optional[Dict[str, str]] = generate_target_script(
        windfile=windfile,
        target=target,
        credentials=CICredentials(url=payload.url, username=payload.username, token=payload.token))
    # generated = {}
    return generated
