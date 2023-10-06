import typing

import argparse

from classes.translator import BambooTranslator
from classes.generated.definitions import Target
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from commands.subcommand import Subcommand


class Translate(Subcommand):
    """
    Translate subcommand. Retrieves the CI job
    from the CI system and translates it into a
    windfile.
    """

    translator: BambooTranslator

    def __init__(
        self,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        url: str,
        token: str,
        args: typing.Any,
    ):
        super().__init__(args)

        self.translator = BambooTranslator(
            input_settings=input_settings, output_settings=output_settings, url=url, token=token
        )

    @staticmethod
    def add_arg_parser(parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for this subcommand to the given parser.
        :param parser:
        """
        parser.add_argument(
            "--key",
            "-k",
            help="Build Plan Key",
            default="AEOLUS-BASE1",
            required=True,
            type=str,
        )

        parser.add_argument(
            "--url",
            help="URL of the Bamboo Server",
            required=True,
            type=str,
        )
        parser.add_argument(
            "--token",
            "-t",
            help="Auth token for the Bamboo Server",
            required=True,
            type=str,
        )

    def translate(self, plan_key: str) -> None:
        """
        Generate the CI file.
        """
        self.translator.translate(plan_key=plan_key)
