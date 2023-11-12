"""
Base class for subcommands.
"""
import argparse
import typing


class Subcommand:
    """
    Base class for subcommands.
    """

    args: typing.Any

    def __init__(self, args: typing.Any):
        self.args = args

    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser) -> None:
        pass
