"""
Merge subcommand.
Merges the given windfile by inlining the external actions.
So that the windfile can be used without dependencies and all files are in the same format and file.
"""
import typing
from typing import Optional

import argparse
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.output_settings import OutputSettings
from classes.validator import (
    Validator,
)
from commands.subcommand import Subcommand
from cli_utils import logger


class Merge(Subcommand):
    """
    Merges the given windfile by inlining the external actions.
    So that the windfile can be
    used without dependencies and all files are in the same format and file.
    """

    merger: Merger

    def __init__(
        self,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        args: typing.Any,
    ):
        super().__init__(args)
        validator: Validator = Validator(output_settings=output_settings, input_settings=input_settings)
        validated: Optional[WindFile] = validator.validate_wind_file()
        if validated:
            self.windfile = validated
            self.merger = Merger(
                windfile=validated,
                input_settings=input_settings,
                output_settings=output_settings,
                metadata=validator.metadata,
            )
        else:
            if output_settings.verbose:
                logger.error("❌", "Validation failed. Aborting.", output_settings.emoji)

    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser) -> None:
        """
        Adds the arguments to the given parser.
        :param parser:
        """
        parser.add_argument(
            "--no-external",
            "-w",
            help="Do not inline external actions.",
            action="store_true",
        )
        # pylint: disable=duplicate-code
        parser.add_argument(
            "--input",
            "-i",
            help="Input file to read from",
            default="windfile.yaml",
            required=True,
            type=open,
        )

    def merge(self) -> Optional[WindFile]:
        return self.merger.merge()
