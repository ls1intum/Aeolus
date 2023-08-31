import logging
import unittest
from typing import Optional

from classes.generated.actionfile import ActionFile
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.metadata import PassMetadata
from classes.output_settings import OutputSettings
from classes.validator import Validator, read_action_file
from test.actionfile_definitions import (
    VALID_ACTIONFILE_WITH_TWO_ACTIONS,
    INVALID_ACTIONFILE_WITH_ONE_ACTION,
)
from test.testutils import TemporaryFileWithContent
from test.windfile_definitions import (
    INVALID_WINDFILE_INTERNAL_ACTION,
    VALID_WINDFILE_INTERNAL_ACTION,
)


class ValidateTests(unittest.TestCase):
    output_settings: OutputSettings

    def setUp(self) -> None:
        """
        Set up the test cases
        """
        logging.basicConfig(
            encoding="utf-8", level=logging.DEBUG, format="%(message)s"
        )
        self.output_settings = OutputSettings(
            verbose=True, debug=True, emoji=True
        )

    def test_validate_no_external_actions(self):
        with TemporaryFileWithContent(content=VALID_WINDFILE_INTERNAL_ACTION) as file:
            validator: Validator = Validator(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=OutputSettings(),
                metadata=PassMetadata(),
            )
            windfile: Optional[WindFile] = validator.validate_wind_file()
            self.assertIsNotNone(windfile)

    def test_validating_invalid_file(self):
        with TemporaryFileWithContent(content=INVALID_WINDFILE_INTERNAL_ACTION) as file:
            valid: Validator = Validator(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=OutputSettings(),
                metadata=PassMetadata(),
            )
            windfile: Optional[WindFile] = valid.validate_wind_file()
            self.assertIsNone(windfile)

    def test_validate_actionfile(self):
        with TemporaryFileWithContent(
            content=VALID_ACTIONFILE_WITH_TWO_ACTIONS
        ) as file:
            valid: Validator = Validator(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=self.output_settings,
                metadata=PassMetadata(),
            )
            action_file: Optional[ActionFile] = valid.validate_action_file()
            self.assertIsNotNone(action_file)

    def test_read_invalid_actionfile(self):
        with TemporaryFileWithContent(
            content=INVALID_ACTIONFILE_WITH_ONE_ACTION
        ) as file:
            action_file: Optional[ActionFile] = read_action_file(
                file=file, output_settings=self.output_settings
            )
            self.assertIsNone(action_file)


if __name__ == "__main__":
    unittest.main()
