import logging
import unittest
from typing import Optional

from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.pass_metadata import PassMetadata
from classes.output_settings import OutputSettings
from generators.cli import CliGenerator
from generators.jenkins import JenkinsGenerator
from test.testutils import TemporaryFileWithContent
from test.windfile_definitions import (
    VALID_WINDFILE_INTERNAL_ACTION,
)


class GenerateTests(unittest.TestCase):
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

    def test_generate_valid_cli_script(self) -> None:
        with TemporaryFileWithContent(VALID_WINDFILE_INTERNAL_ACTION) as file:
            metadata: PassMetadata = PassMetadata()
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=self.output_settings,
                metadata=metadata,
            )
            cli: CliGenerator = CliGenerator(
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=self.output_settings,
                windfile=merger.merge(),
                metadata=metadata,
            )
            result: str = cli.generate()
            self.assertTrue(result.count("#!/usr/bin/env bash") == 1)
            self.assertTrue("set -e" in result)
            self.assertTrue("set -x" in result)
            # two comments, one definition and one call
            self.assertTrue(result.count("internal-action") == 4)
            self.assertTrue(result.count("{") == result.count("}"))
            self.assertTrue(cli.check(content=result))

    def test_generate_jenkinsfile(self) -> None:
        with TemporaryFileWithContent(VALID_WINDFILE_INTERNAL_ACTION) as file:
            metadata: PassMetadata = PassMetadata()
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=self.output_settings,
                metadata=metadata,
            )
            windfile: Optional[WindFile] = merger.merge()
            self.assertIsNotNone(windfile)
            jenkins: JenkinsGenerator = JenkinsGenerator(
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=self.output_settings,
                windfile=windfile,
                metadata=metadata,
            )
            result: str = jenkins.generate()
            self.assertTrue(result.count("pipeline {") == 1)
            self.assertTrue(result.count("{") == result.count("}"))


if __name__ == "__main__":
    unittest.main()
