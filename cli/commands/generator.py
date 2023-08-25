import argparse

from commands.subcommand import Subcommand


class Generator(Subcommand):
    """
    Generator subcommand. Generates a platform specific CI file from a windfile.
    The windfile is validated and merged before generating the CI file for simplicity.
    """
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

    def generate(self) -> None:
        """
        Generate the CI file.
        """
        pass
