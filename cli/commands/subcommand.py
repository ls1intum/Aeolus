import argparse
import typing


class Subcommand:
    args: typing.Any

    def __init__(self, args: typing.Any):
        self.args = args

    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser) -> None:
        pass
