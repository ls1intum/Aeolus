import argparse

from commands.subcommand import Subcommand


class Generator(Subcommand):
    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser) -> None:
        pass

    def generate(self) -> None:
        pass
