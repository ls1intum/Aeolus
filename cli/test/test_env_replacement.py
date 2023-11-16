import logging
import unittest
from typing import Optional, List, Union, Type

from test.windfile_definitions import (
    VALID_WINDFILE_WITH_ENV_VARIABLES_AND_DOCKER, VALID_WINDFILE_WITH_MULTIPLE_REPOSITORIES,
)
from generators.bamboo import BambooGenerator
from generators.base import BaseGenerator
from generators.cli import CliGenerator
from generators.jenkins import JenkinsGenerator
from classes.generated.environment import EnvironmentSchema
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.pass_metadata import PassMetadata
from classes.output_settings import OutputSettings
from cli_utils.utils import TemporaryFileWithContent


class EnvironmentReplacementTests(unittest.TestCase):
    output_settings: OutputSettings

    def setUp(self) -> None:
        """
        Set up the test cases
        """
        logging.basicConfig(encoding="utf-8", level=logging.DEBUG, format="%(message)s")
        self.output_settings = OutputSettings(verbose=True, debug=True, emoji=True)

    def test_replace_all_env_variables_jenkins(self) -> None:
        self.generate_and_check_if_all_env_variables_are_replaced(generator=JenkinsGenerator)

    def test_replace_all_env_variables_bamboo(self) -> None:
        self.generate_and_check_if_all_env_variables_are_replaced(generator=BambooGenerator)

    def test_replace_all_env_variables_cli(self) -> None:
        self.generate_and_check_if_all_env_variables_are_replaced(generator=CliGenerator)

    def test_set_repository_env_variables_jenkins(self) -> None:
        self.generate_and_check_if_repository_variables_are_set(generator=JenkinsGenerator)

    def test_set_repository_env_variables_cli(self) -> None:
        self.generate_and_check_if_repository_variables_are_set(generator=CliGenerator)

    def generate_and_check_if_all_env_variables_are_replaced(
            self, generator: Union[Type[JenkinsGenerator] | Type[CliGenerator] | Type[BambooGenerator]]
    ) -> None:
        """
        Generates a file with the given generator and checks if all environment variables are replaced
        :param generator: Generator to use
        """
        with TemporaryFileWithContent(content=VALID_WINDFILE_WITH_ENV_VARIABLES_AND_DOCKER) as file:
            metadata = PassMetadata()
            merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=self.output_settings,
                metadata=metadata,
            )
            windfile: Optional[WindFile] = merger.merge()
            self.assertIsNotNone(windfile)
            if windfile is None:
                self.fail("Windfile is None")
            gen: BaseGenerator = generator(
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=self.output_settings,
                windfile=windfile,
                metadata=metadata,
            )
            env_vars: EnvironmentSchema = gen.environment
            result: str = gen.generate()
            if windfile is None:
                self.fail("Windfile is None")
            self.check_if_all_env_variables_are_replaced(result=result, env_vars=env_vars)

    def generate_and_check_if_repository_variables_are_set(
            self, generator: Union[Type[JenkinsGenerator] | Type[CliGenerator]]
    ) -> None:
        """
        Generates a file with the given generator and checks if repository variables are set, only relevant for
        Jenkins and CLI
        :param generator: Generator to use
        """
        with TemporaryFileWithContent(content=VALID_WINDFILE_WITH_MULTIPLE_REPOSITORIES) as file:
            metadata = PassMetadata()
            merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=self.output_settings,
                metadata=metadata,
            )
            windfile: Optional[WindFile] = merger.merge()
            self.assertIsNotNone(windfile)
            if windfile is None:
                self.fail("Windfile is None")
            gen: BaseGenerator = generator(
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=self.output_settings,
                windfile=windfile,
                metadata=metadata,
            )
            result: str = gen.generate()
            if windfile is None:
                self.fail("Windfile is None")

            if isinstance(gen, JenkinsGenerator):
                index: int = 0
                for repo in windfile.repositories.values():
                    var_name: str = f"REPOSITORY_URL"
                    if index > 0:
                        var_name += f"_{index}"
                    self.assertIn(f"{var_name} = '{repo.url}'", result)
                    self.assertIn("url: '${" + var_name + "}'", result)
                    index += 1
            elif isinstance(gen, CliGenerator):
                index: int = 0
                for repo in windfile.repositories.values():
                    var_name: str = f"REPOSITORY_URL"
                    if index > 0:
                        var_name += f"_{index}"
                    self.assertIn(f'export {var_name}="{repo.url}"', result)
                    index += 1



    def check_if_all_env_variables_are_replaced(self, result: str, env_vars: EnvironmentSchema) -> None:
        """
        Checks if all environment variables are replaced in the generated result
        :param result: Target result to check
        :param env_vars: Environment variables for target and their replacement
        """
        allowed: List[str] = [env_vars.__dict__[e] for e in env_vars.__dict__.keys()]
        forbidden_with_none: List[Optional[str]] = [e if e not in allowed else None for e in env_vars.__dict__.keys()]
        forbidden: List[str] = [e for e in forbidden_with_none if e is not None]
        self.assertFalse(all(e not in result for e in forbidden))
        self.assertTrue(any(e in result for e in allowed))


if __name__ == "__main__":
    unittest.main()
