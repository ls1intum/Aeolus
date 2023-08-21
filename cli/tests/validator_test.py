import os
import typing

import unittest

from classes.generated.actionfile import ActionFile
from commands.validator import Validator, has_external_actions
from main import parse_args
from classes.generated.windfile import WindFile


class ValidatorTest(unittest.TestCase) -> None:
    def test_valid_windfile(self):
        path: str = os.path.dirname(os.path.realpath(__file__))
        parsed_arguments: typing.Any = parse_args(
            arguments=[
                "validate",
                "-w",
                "-i",
                os.path.join(path, "files", "valid-windfile.yml"),
            ]
        )
        validator: Validator = Validator(args=parsed_arguments)
        self.assertTrue(validator.validate())

    def test_valid_windfile_verbose(self) -> None:
        path: str = os.path.dirname(os.path.realpath(__file__))
        parsed_arguments: typing.Any = parse_args(
            arguments=[
                "-v",
                "validate",
                "-w",
                "-i",
                os.path.join(path, "files", "valid-windfile.yml"),
            ]
        )
        validator: Validator = Validator(args=parsed_arguments)
        self.assertTrue(validator.validate())

    def test_invalid_windfile(self) -> None:
        path: str = os.path.dirname(os.path.realpath(__file__))
        parsed_arguments: typing.Any = parse_args(
            arguments=[
                "validate",
                "-w",
                "-i",
                os.path.join(path, "files", "invalid-windfile.yml"),
            ]
        )
        validator: Validator = Validator(args=parsed_arguments)
        self.assertFalse(validator.validate())

    def test_invalid_windfile_verbose(self) -> None:
        path: str = os.path.dirname(os.path.realpath(__file__))
        parsed_arguments: typing.Any = parse_args(
            arguments=[
                "-v",
                "-d",
                "validate",
                "-w",
                "-i",
                os.path.join(path, "files", "invalid-windfile.yml"),
            ]
        )
        validator: Validator = Validator(args=parsed_arguments)
        self.assertFalse(validator.validate())

    def test_external_actions_detection(self) -> None:
        path: str = os.path.dirname(os.path.realpath(__file__))
        parsed_arguments: typing.Any = parse_args(
            arguments=[
                "-v",
                "-d",
                "validate",
                "-w",
                "-i",
                os.path.join(
                    path, "files", "windfile-with-external-action.yml"
                ),
            ]
        )
        validator: Validator = Validator(args=parsed_arguments)
        windfile: ActionFile | WindFile | None = validator.validate()
        self.assertIsInstance(windfile, WindFile)
        self.assertTrue(windfile)
        if isinstance(windfile, WindFile):
            self.assertTrue(has_external_actions(windfile))

    def test_no_external_actions_detection(self) -> None:
        path: str = os.path.dirname(os.path.realpath(__file__))
        parsed_arguments: typing.Any = parse_args(
            arguments=[
                "validate",
                "-w",
                "-i",
                os.path.join(path, "files", "valid-windfile.yml"),
            ]
        )
        validator: Validator = Validator(args=parsed_arguments)
        windfile: ActionFile | WindFile | None = validator.validate()
        self.assertIsInstance(windfile, WindFile)
        self.assertTrue(windfile)
        if isinstance(windfile, WindFile):
            self.assertFalse(has_external_actions(windfile))

    def test_valid_actionfile(self) -> None:
        path: str = os.path.dirname(os.path.realpath(__file__))
        parsed_arguments: typing.Any = parse_args(
            arguments=[
                "-v",
                "-d",
                "validate",
                "-a",
                "-i",
                os.path.join(path, "files", "simple-action.yml"),
            ]
        )
        validator: Validator = Validator(args=parsed_arguments)
        self.assertTrue(validator.validate())


if __name__ == "__main__":
    unittest.main()
