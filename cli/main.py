import logging

import argparse
import sys

from commands.generator import Generator
from commands.merge import Merge
from commands.validate import Validate


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
    Generator.add_arg_parser(parser=generator_parser)
    return arg_parser


if __name__ == "__main__":
    logger = logging.getLogger("aeolus")
    parser: argparse.ArgumentParser = add_argparse()
    args = parser.parse_args(sys.argv[1:])
    if args.verbose:
        logging.basicConfig(
            encoding="utf-8", level=logging.INFO, format="%(message)s"
        )
    if args.debug:
        logging.basicConfig(
            encoding="utf-8", level=logging.DEBUG, format="%(message)s"
        )

    if args.command == "validate":
        validator: Validate = Validate(args=args)
        validator.validate()
    if args.command == "merge":
        merger: Merge = Merge(args=args)
        merger.merge()
    if args.command == "generate":
        generator: Generator = Generator(args=args)
        generator.generate()
    if args.command is None:
        parser.print_help()
