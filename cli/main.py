import argparse
import sys

from commands.merger import Merger
from commands.validator import Validator


def add_argparse() -> argparse.ArgumentParser:
    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="aeolus",
        description="Aeolus is a tool to manage your CI jobs. It allows you to define your jobs in a simple "
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

    validate_parser = subparsers.add_parser(name="validate")
    Validator.add_arg_parser(parser=validate_parser)

    merger_parser = subparsers.add_parser(name="merge")
    Merger.add_arg_parser(parser=merger_parser)
    return arg_parser


if __name__ == "__main__":
    parser: argparse.ArgumentParser = add_argparse()
    args = parser.parse_args(sys.argv[1:])
    if args.command == "validate":
        validator: Validator = Validator(args=args)
        validator.validate()
    if args.command == "merge":
        merger: Merger = Merger(args=args)
        merger.merge()
