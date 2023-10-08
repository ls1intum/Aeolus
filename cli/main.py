#!/usr/bin/env python3
import logging
import typing
from io import TextIOWrapper

import argparse
import sys

from classes.ci_credentials import CICredentials
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from commands.generate import Generate
from commands.merge import Merge
from commands.translate import Translate
from commands.validate import Validate
from utils import utils


def add_argparse() -> argparse.ArgumentParser:
    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="aeolus",
        description="Aeolus is a tool to manage your CI jobs. "
        "It allows you to define your jobs in a simple "
        "manner and execute them on multiple CI systems.",
    )
    subparsers = arg_parser.add_subparsers(dest="command")
    arg_parser.add_argument(
        "--verbose",
        "-v",
        help="Increase output verbosity",
        action="store_true",
    )
    arg_parser.add_argument(
        "--version",
        "-V",
        help="Print version and exit",
        action="version",
        version="%(prog)s v0.0.1",
    )
    arg_parser.add_argument(
        "--debug",
        "-d",
        help="Enable debug mode",
        action="store_true",
    )
    arg_parser.add_argument(
        "--emoji",
        "-e",
        help="Enable emoji mode",
        action="store_true",
    )

    validate_parser = subparsers.add_parser(name="validate")
    Validate.add_arg_parser(parser=validate_parser)

    merger_parser = subparsers.add_parser(name="merge")
    Merge.add_arg_parser(parser=merger_parser)

    generator_parser = subparsers.add_parser(name="generate")
    Generate.add_arg_parser(parser=generator_parser)

    bamboo_translator_parser = subparsers.add_parser(name="translate")
    Translate.add_arg_parser(parser=bamboo_translator_parser)
    return arg_parser


def parse_args(arguments: list[str]) -> typing.Any:
    argument_parser: argparse.ArgumentParser = add_argparse()
    return argument_parser.parse_args(arguments)


if __name__ == "__main__":
    logger = logging.getLogger("aeolus")
    parser: argparse.ArgumentParser = add_argparse()
    args = parser.parse_args(sys.argv[1:])
    if args.debug:
        logging.basicConfig(encoding="utf-8", level=logging.DEBUG, format="%(message)s")
    if args.verbose:
        logging.basicConfig(encoding="utf-8", level=logging.INFO, format="%(message)s")
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    output_settings: OutputSettings = OutputSettings(
        verbose=args.verbose, debug=args.debug, emoji=args.emoji, ci_credentials=None
    )
    file_path: str = args.key if "translate" == args.command else args.input.name
    file: typing.Optional[TextIOWrapper] = None if "translate" == args.command else args.input
    input_settings: InputSettings = InputSettings(file_path=file_path, file=file)

    if args.command == "validate":
        validator: Validate = Validate(
            input_settings=input_settings,
            output_settings=output_settings,
            args=args,
        )
        validator.validate()
    if args.command == "merge":
        merger: Merge = Merge(
            input_settings=input_settings,
            output_settings=output_settings,
            args=args,
        )
        merger.merge()
    if args.command == "generate":
        if args.publish:
            if not args.url or not args.token:
                utils.logger.error(
                    "❌ ",
                    "Publishing requires a CI URL and a token",
                    output_settings.emoji,
                )
                raise ValueError("Publishing requires a Bamboo URL and a token")
            output_settings.ci_credentials = CICredentials(url=args.url, token=args.token)

        generator: Generate = Generate(
            input_settings=input_settings,
            output_settings=output_settings,
            args=args,
        )
        generator.generate()
    if args.command == "translate":
        credentials: CICredentials = CICredentials(url=args.url, token=args.token)
        translator: Translate = Translate(
            input_settings=input_settings, output_settings=output_settings, credentials=credentials, args=args
        )
        translator.translate(plan_key=args.key)
