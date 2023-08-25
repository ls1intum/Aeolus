import os
import traceback
import typing
from typing import Optional, Tuple, List

import argparse
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.output_settings import OutputSettings
from commands.subcommand import Subcommand
from classes.validator import (
    Validator,
)
from utils import logger


class Merge(Subcommand):
    """
    Merges the given windfile by inlining the external actions. So that the windfile can be
    used without dependencies and all files are in the same format and file.
    """

    merger: Merger

    def __init__(self, args: typing.Any):
        super().__init__(args)
        output_settings: OutputSettings = OutputSettings(
            verbose=args.verbose, debug=args.debug, emoji=args.emoji
        )
        input_settings: InputSettings = InputSettings(
            file_path=args.input.name, file=args.input
        )
        validator: Validator = Validator(
            output_settings=output_settings, input_settings=input_settings
        )
        validated: Optional[WindFile] = validator.validate_wind_file()
        if validated:
            self.windfile = validated
            self.merger = Merger(
                windfile=validated,
                input_settings=input_settings,
                output_settings=output_settings,
            )
        else:
            if output_settings.verbose:
                logger.error(
                    "❌", "Validation failed. Aborting.", output_settings.emoji
                )

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
