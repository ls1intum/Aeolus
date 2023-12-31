#!/usr/bin/env python3
"""
Main file of the tool. This file contains the main function and the argparser.
"""
import logging
import sys
import typing
from io import TextIOWrapper

import argparse

from classes.ci_credentials import CICredentials
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.run_settings import RunSettings
from cli_utils import utils
from commands.generate import Generate
from commands.merge import Merge
from commands.translate import Translate
from commands.validate import Validate


def add_argparse() -> argparse.ArgumentParser:
    """
    Add arguments and subcommands to the argparser of the tool.
    :return: argparser with arguments and subcommands
    """
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
    """
    Parse the given arguments.
    :param arguments:
    :return:
    """
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
                    "Publishing requires a CI URL and a token, with Jenkins we also need a username",
                    output_settings.emoji,
                )
                raise ValueError("Publishing requires a CI URL and a token, with Jenkins we also need a username")
            output_settings.ci_credentials = CICredentials(url=args.url, username=args.user, token=args.token)

        if args.run is not None:
            if args.target != "cli" and (not args.url or not args.token):
                utils.logger.error(
                    "❌ ",
                    "Running is only supported for Jenkins and Bamboo"
                    " if you use also pass a ci url (--url) and token (--token)",
                    output_settings.emoji,
                )
                raise ValueError(f"Running in {args.target} is only supported with credentials")
            if args.target == "cli" or (args.url and args.token):
                output_settings.run_settings = RunSettings(stage=args.run)

        generator: Generate = Generate(
            input_settings=input_settings,
            output_settings=output_settings,
            args=args,
        )
        generator.generate()

    if args.command == "translate":
        credentials: CICredentials = CICredentials(url=args.url, username=None, token=args.token)
        translator: Translate = Translate(
            input_settings=input_settings, output_settings=output_settings, credentials=credentials, args=args
        )
        translator.translate(plan_key=args.key)
