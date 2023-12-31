"""
Generator class. This class is responsible for generating the CI file from the given windfile.
"""
from typing import Optional

from classes.generated.definitions import (
    Target,
)
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.output_settings import OutputSettings
from classes.pass_settings import PassSettings
from classes.validator import Validator
from cli_utils import logger
from generators.bamboo import BambooGenerator
from generators.cli import CliGenerator
from generators.jenkins import JenkinsGenerator


class Generator(PassSettings):
    check_syntax: bool
    target: Target
    publish: bool

    def __init__(
        self, input_settings: InputSettings, output_settings: OutputSettings, target: Target, check_syntax: bool
    ):
        validator: Validator = Validator(output_settings=output_settings, input_settings=input_settings)
        validated: Optional[WindFile] = validator.validate_wind_file()
        if validated:
            self.windfile = validated
        merger: Merger = Merger(
            windfile=validated,
            input_settings=input_settings,
            output_settings=output_settings,
            metadata=validator.metadata,
        )
        windfile: Optional[WindFile] = merger.merge()
        if not windfile:
            logger.error("❌ ", "Merging failed. Aborting.", output_settings.emoji)
            raise ValueError("Merging failed.")

        super().__init__(
            input_settings,
            output_settings,
            windfile=windfile,
            metadata=merger.metadata,
        )

        self.target = target
        self.check_syntax = check_syntax

    def generate(self) -> Optional[str]:
        """
        Generates the CI file from the given windfile.
        :return:
        """
        if not self.windfile:
            logger.error("❌ ", "Merging failed. Aborting.", self.output_settings.emoji)
            return None

        actual_generator: Optional[CliGenerator | JenkinsGenerator | BambooGenerator] = None
        if self.target == Target.cli.name:
            actual_generator = CliGenerator(
                windfile=self.windfile,
                input_settings=self.input_settings,
                output_settings=self.output_settings,
                metadata=self.metadata,
            )
        if self.target == Target.jenkins.name:
            actual_generator = JenkinsGenerator(
                windfile=self.windfile,
                input_settings=self.input_settings,
                output_settings=self.output_settings,
                metadata=self.metadata,
            )
        if self.target == Target.bamboo.name:
            actual_generator = BambooGenerator(
                windfile=self.windfile,
                input_settings=self.input_settings,
                output_settings=self.output_settings,
                metadata=self.metadata,
            )
        if actual_generator:
            result: str = actual_generator.generate()
            if self.output_settings.verbose:
                logger.info(
                    "📄",
                    f"Generated {self.target} pipeline:",
                    self.output_settings.emoji,
                )
            print(result)
            if self.check_syntax:
                if actual_generator.check(result):
                    logger.info(
                        "✅ ",
                        "Syntax check passed",
                        self.output_settings.emoji,
                    )
                else:
                    logger.error(
                        "❌ ",
                        "Syntax check failed",
                        self.output_settings.emoji,
                    )
            if (
                self.output_settings.run_settings is not None
                and self.windfile is not None
                and self.windfile.metadata is not None
                and (self.windfile.metadata.id is not None or self.target == Target.cli.value)
            ):
                actual_generator.run(job_id=self.windfile.metadata.id)
            return actual_generator.key
        return None

    def run(self, job_id: str) -> None:
        """
        Run the generated CI file.
        :param job_id: ID of the job to run
        :return: None
        """
        raise NotImplementedError("run() not implemented")
