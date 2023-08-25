import typing
from typing import Optional

import argparse

from classes.generated.actionfile import ActionFile
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.validator import Validator
from commands.subcommand import Subcommand


class Validate(Subcommand):

    validator: Validator

    def __init__(self, args: typing.Any):
        super().__init__(args)
        output_settings: OutputSettings = OutputSettings(
            verbose=args.verbose, debug=args.debug, emoji=True
        )
        input_settings: InputSettings = InputSettings(
            file_path=args.input.name, file=args.input
        )
        self.validator: Validator = Validator(input_settings=input_settings, output_settings=output_settings)

    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--wind", "-w", help="Validate windfile.", action="store_true"
        )
        parser.add_argument(
            "--action", "-a", help="Validate action.", action="store_true"
        )
        parser.add_argument(
            "--input",
            "-i",
            help="Input file to read from",
            default="windfile.yaml",
            required=True,
            type=open,
        )  # pylint: disable=duplicate-code

    def validate(self) -> ActionFile | WindFile | None:
        """
        Validates the given file. If the file is valid,
        the read object is returned.
        If the file is invalid, None is returned.
        :return: ActionFile or WindFile or None
        """
        if self.args.wind:
            return self.validator.validate_wind_file()
        if self.args.action:
            return self.validator.validate_action_file()
        return None
