# pylint: skip-file
import os
import time
import typing

import yaml

from classes.ci_credentials import CICredentials
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.translator import BambooTranslator
from classes.yaml_dumper import YamlDumper
from cli_utils import logger

@typing.no_type_check
def get_build_plans() -> typing.List[typing.Tuple[str, str]]:
    """
    Get all build plans from Bamboo.
    :return: list of build plans
    """
    plans: typing.List[typing.Tuple[str, str]] = []
    with open("extracted_build_plans.txt", "r", encoding="utf-8") as content:
        for line in content:
            name: str = line.split(";")[0]
            date: str = line.split(";")[1]
            plans.append((name, date))
    return plans

@typing.no_type_check
def read_env_vars() -> dict[str, str]:
    """
    Read the token from the env file.
    :return: token
    """
    credentials: dict[str, str] = {}
    with open(".env", "r", encoding="utf-8") as content:
        for line in content:
            key: str = line.split("=")[0]
            value: str = line.split("=")[1].replace("\n", "")
            credentials[key] = value
    return credentials

@typing.no_type_check
def main() -> None:
    # pylint: disable=too-many-locals
    plans: typing.List[typing.Tuple[str, str]] = get_build_plans()
    input_settings: InputSettings = InputSettings(file_path="extracted_build_plans.txt")
    output_settings: OutputSettings = OutputSettings()
    credentials: dict[str, str] = read_env_vars()
    token: str = credentials["BAMBOO_TOKEN"]
    username: str = credentials["BAMBOO_USERNAME"]
    url: str = credentials["BAMBOO_URL"]
    translationtimes: dict[str, float] = {}
    failed_plans: list[str] = []
    translator: BambooTranslator = BambooTranslator(
        input_settings=input_settings, output_settings=output_settings, credentials=CICredentials(url, username, token)
    )
    if not os.path.exists("translated_plans"):
        os.mkdir("translated_plans")
    sleep_counter: int = 0
    print(f"Found {len(plans)} build plans")
    for plan in plans:
        if os.path.exists(f"translated_plans/{plan[0]}.yaml"):
            print(f"Skipping {plan[0]} as it already exists")
            continue
        try:
            start = time.time()
            windfile: typing.Optional[WindFile] = translator.translate(plan_key=plan[0])
            end = time.time()
            print(f"Translated plan in {end - start}s")
            translationtimes[plan[0]] = end - start
            if windfile is None:
                print(f"could not translate plan {plan[0]}")
                continue
            with open(f"translated_plans/{plan[0]}.yaml", "w") as content:
                # work-around as enums do not get cleanly printed with model_dump
                json: str = windfile.model_dump_json(exclude_none=True)
                logger.info("🪄", "Translated windfile", output_settings.emoji)
                content.write(
                    yaml.dump(yaml.safe_load(json), sort_keys=False, Dumper=YamlDumper, default_flow_style=False)
                )
            sleep_counter += 1
            if sleep_counter == 1000:
                print("Sleeping for 5 seconds...")
                time.sleep(1)
        except Exception:
            print(f"Could not translate plan {plan[0]}")
            failed_plans.append(plan[0])
            continue
        print(f"{sleep_counter}/{len(plans)} Done")
    with open("translation_times.txt", "w", encoding="utf-8") as content:
        for key, value in translationtimes.items():
            content.write(f"{key};{value}\n")
    with open("failed_plans.txt", "w", encoding="utf-8") as content:
        for plan in failed_plans:
            content.write(f"{plan}\n")


if __name__ == "__main__":
    main()
