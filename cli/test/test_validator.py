import logging
import os
import typing
import unittest

from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings
from classes.validator import has_external_actions
from classes.generated.actionfile import ActionFile
from classes.generated.windfile import WindFile
from main import parse_args
from commands.validate import Validate


class ValidatorTest(unittest.TestCase):
    output_settings: OutputSettings

    def setUp(self) -> None:
        """
        Set up the test cases
        """
        logging.basicConfig(encoding="utf-8", level=logging.DEBUG, format="%(message)s")
        self.output_settings = OutputSettings(verbose=True, debug=True, emoji=True)

    def test_valid_windfile(self) -> None:
        path: str = os.path.dirname(os.path.realpath(__file__))
        parsed_arguments: typing.Any = parse_args(
            arguments=[
                "validate",
                "-w",
                "-i",
                os.path.join(path, "files", "valid-windfile.yml"),
            ]
        )
        input_settings: InputSettings = InputSettings(
            file_path=parsed_arguments.input.name, file=parsed_arguments.input
        )
        validator: Validate = Validate(
            input_settings=input_settings, output_settings=self.output_settings, args=parsed_arguments
        )
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
        input_settings: InputSettings = InputSettings(
            file_path=parsed_arguments.input.name, file=parsed_arguments.input
        )
        validator: Validate = Validate(
            input_settings=input_settings, output_settings=self.output_settings, args=parsed_arguments
        )
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
        input_settings: InputSettings = InputSettings(
            file_path=parsed_arguments.input.name, file=parsed_arguments.input
        )
        validator: Validate = Validate(
            input_settings=input_settings, output_settings=self.output_settings, args=parsed_arguments
        )
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
        input_settings: InputSettings = InputSettings(
            file_path=parsed_arguments.input.name, file=parsed_arguments.input
        )
        validator: Validate = Validate(
            input_settings=input_settings, output_settings=self.output_settings, args=parsed_arguments
        )
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
                os.path.join(path, "files", "windfile-with-file-action.yml"),
            ]
        )
        input_settings: InputSettings = InputSettings(
            file_path=parsed_arguments.input.name, file=parsed_arguments.input
        )
        validator: Validate = Validate(
            input_settings=input_settings, output_settings=self.output_settings, args=parsed_arguments
        )
        windfile: ActionFile | WindFile | None = validator.validate()
        self.assertIsInstance(windfile, WindFile)
        self.assertIsNotNone(windfile)
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
        input_settings: InputSettings = InputSettings(
            file_path=parsed_arguments.input.name, file=parsed_arguments.input
        )
        validator: Validate = Validate(
            input_settings=input_settings, output_settings=self.output_settings, args=parsed_arguments
        )
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
        input_settings: InputSettings = InputSettings(
            file_path=parsed_arguments.input.name, file=parsed_arguments.input
        )
        validator: Validate = Validate(
            input_settings=input_settings, output_settings=self.output_settings, args=parsed_arguments
        )
        self.assertTrue(validator.validate())


if __name__ == "__main__":
    unittest.main()
