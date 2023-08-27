import typing

import argparse

from classes.generator import Generator
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from commands.subcommand import Subcommand


class Generate(Subcommand):
    """
    Generate subcommand. Generates a platform specific CI
    file from a windfile.
    The windfile is validated and merged before generating
    the CI file for simplicity.
    """

    generator: Generator

    def __init__(
        self,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        args: typing.Any,
    ):
        super().__init__(args)

        self.generator = Generator(
            input_settings=input_settings,
            output_settings=output_settings,
            target=self.args.target,
        )

    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for this subcommand to the given parser.
        :param parser:
        """
        parser.add_argument(
            "--input",
            "-i",
            help="Input file to read from",
            default="windfile.yaml",
            required=True,
            type=open,
        )

        parser.add_argument(
            "--target",
            "-t",
            help="Target CI system",
            required=True,
            choices=["cli"],
        )

    def generate(self) -> None:
        """
        Generate the CI file.
        """
        self.generator.generate()
