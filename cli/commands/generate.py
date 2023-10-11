import typing

import argparse

from classes.generated.definitions import Lifecycle
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
            check_syntax=self.args.check,
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
            choices=["cli", "jenkins", "bamboo"],
        )

        parser.add_argument(
            "--check",
            "-c",
            help="Check the generated file for syntax errors",
            action="store_true",
        )

        parser.add_argument(
            "--publish",
            "-p",
            help="Publish the generated file to the CI system",
            action="store_true",
        )

        parser.add_argument(
            "--url",
            help="URL of the CI Server",
            type=str,
        )

        parser.add_argument(
            "--user",
            help="Username to be used in the CI system",
            type=str,
        )

        parser.add_argument(
            "--token",
            help="Auth token for the CI Server",
            type=str,
        )

        parser.add_argument(
            "--run", "-r", help="Run the generated file on the CI system", choices=Lifecycle.__members__.keys()
        )

    def generate(self) -> None:
        """
        Generate the CI file.
        """
        self.generator.generate()

    def run(self, job_id: str) -> None:
        """
        Run the generated CI file on the CI system.
        :param job_id: ID of the job to run
        """
        self.generator.run(job_id=job_id)
