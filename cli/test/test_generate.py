import logging
import unittest
from typing import Optional

from test.windfile_definitions import (
    VALID_WINDFILE_INTERNAL_ACTION,
)
from classes.generated.definitions import Target
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.pass_metadata import PassMetadata
from classes.output_settings import OutputSettings
from generators.cli import CliGenerator
from generators.jenkins import JenkinsGenerator
from cli_utils.utils import TemporaryFileWithContent


class GenerateTests(unittest.TestCase):
    output_settings: OutputSettings

    def setUp(self) -> None:
        """
        Set up the test cases
        """
        logging.basicConfig(encoding="utf-8", level=logging.DEBUG, format="%(message)s")
        self.output_settings = OutputSettings(verbose=True, debug=True, emoji=True)

    def test_generate_valid_cli_script(self) -> None:
        with TemporaryFileWithContent(VALID_WINDFILE_INTERNAL_ACTION) as file:
            metadata: PassMetadata = PassMetadata()
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name, target=Target.cli),
                output_settings=self.output_settings,
                metadata=metadata,
            )
            windfile: Optional[WindFile] = merger.merge()
            self.assertIsNotNone(windfile)
            if windfile is None:
                self.fail("Windfile is None")
            cli: CliGenerator = CliGenerator(
                input_settings=InputSettings(file=file, file_path=file.name, target=Target.cli),
                output_settings=self.output_settings,
                windfile=windfile,
                metadata=metadata,
            )
            result: str = cli.generate()
            self.assertTrue(result.count("#!/usr/bin/env bash") == 1)
            self.assertTrue("set -e" in result)
            # two comments, one definition, one echo for execution, one echo in the actual action, and one call
            self.assertTrue(result.count("internal-action") == 5)
            self.assertTrue(result.count("{") == result.count("}"))
            self.assertTrue(cli.check(content=result))

    def test_generate_jenkinsfile(self) -> None:
        self.setUp()
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
            if windfile is None:
                self.fail("Windfile is None")
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
