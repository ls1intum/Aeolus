import argparse

from commands.subcommand import Subcommand


class Merger(Subcommand):
    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser):
        parser.add_argument(
            "--no-external",
            "-w",
            help="Do not inline external actions.",
            action="store_true",
        )
        parser.add_argument(
            "--input",
            "-i",
            help="Input file to read from",
            default="windfile.yaml",
            required=True,
            type=open,
        )
