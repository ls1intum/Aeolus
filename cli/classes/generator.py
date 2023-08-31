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
from generators.cli import CliGenerator
from generators.jenkins import JenkinsGenerator
from utils import logger


class Generator(PassSettings):
    check_syntax: bool
    target: Target

    def __init__(
        self,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        target: Target,
        check_syntax: bool,
    ):
        validator: Validator = Validator(
            output_settings=output_settings, input_settings=input_settings
        )
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
            logger.error(
                "❌", "Merging failed. Aborting.", output_settings.emoji
            )
            raise ValueError("Merging failed.")

        super().__init__(
            input_settings,
            output_settings,
            windfile=windfile,
            metadata=merger.metadata,
        )
        self.target = target
        self.check_syntax = check_syntax

    def generate(self) -> None:
        if not self.windfile:
            logger.error(
                "❌", "Merging failed. Aborting.", self.output_settings.emoji
            )
            return None
        # current_action: FileAction | InternalAction | PlatformAction |
        # ExternalAction = self.windfile.jobs[
        #     "hello-world_0"
        # ].root
        # if not isinstance(current_action, InternalAction):
        #     logger.error(
        #         "❌",
        #         "Merging did not result in all internal actions",
        #         self.output_settings.emoji,
        #     )
        #     return
        # action: InternalAction = current_action
        # code: str = action.script
        # print(code)
        # print("calling:")
        # execute_arbitrary_code(code, "build", "hello-world_0")
        actual_generator: Optional[CliGenerator | JenkinsGenerator] = None
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
        if actual_generator:
            result: str = actual_generator.generate()
            if self.output_settings.verbose:
                logger.info(
                    "📄",
                    f"Generated {self.target} pipeline:\n{result}",
                    self.output_settings.emoji,
                )
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
        return None
