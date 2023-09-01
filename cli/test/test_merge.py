import logging
import unittest
from typing import Optional

from test.testutils import TemporaryFileWithContent
from test.actionfile_definitions import VALID_ACTIONFILE_WITH_TWO_ACTIONS
from test.windfile_definitions import (
    VALID_WINDFILE_INTERNAL_ACTION,
    INVALID_WINDFILE_INTERNAL_ACTION,
    VALID_WINDFILE_WITH_NON_EXISTING_ACTIONFILE,
)
from classes.generated.definitions import InternalAction, FileAction, PlatformAction, ExternalAction
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.pass_metadata import PassMetadata
from classes.output_settings import OutputSettings


class MergeTests(unittest.TestCase):
    output_settings: OutputSettings

    def setUp(self) -> None:
        """
        Set up the test cases
        """
        logging.basicConfig(encoding="utf-8", level=logging.DEBUG, format="%(message)s")
        self.output_settings = OutputSettings(verbose=True, debug=True, emoji=True)

    def test_merge_no_external_actions(self) -> None:
        with TemporaryFileWithContent(content=VALID_WINDFILE_INTERNAL_ACTION) as file:
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=OutputSettings(),
                metadata=PassMetadata(),
            )
            windfile: Optional[WindFile] = merger.merge()
            self.assertIsNotNone(windfile)
            if windfile is None:
                self.fail("Windfile is None")
            self.assertEqual(len(windfile.jobs), 1)
            self.assertTrue("internal-action" in windfile.jobs)
            self.assertTrue(isinstance(windfile.jobs["internal-action"].root, InternalAction))
            if isinstance(windfile.jobs["internal-action"].root, InternalAction):
                action: InternalAction = windfile.jobs["internal-action"].root
                self.assertEqual(action.script, 'echo "This is an internal action"')
            else:
                self.fail("Action is not an instance of InternalAction, but should be")

    def test_merging_invalid_file(self) -> None:
        with TemporaryFileWithContent(content=INVALID_WINDFILE_INTERNAL_ACTION) as file:
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=OutputSettings(),
                metadata=PassMetadata(),
            )
            windfile = merger.merge()
            self.assertIsNone(windfile)

    def test_merging_nonexisting_file(self) -> None:
        with TemporaryFileWithContent(content=VALID_WINDFILE_WITH_NON_EXISTING_ACTIONFILE) as file:
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=OutputSettings(),
                metadata=PassMetadata(),
            )
            windfile: Optional[WindFile] = merger.merge()
            self.assertIsNone(windfile)

    def test_merge_with_external_actions(self) -> None:
        with TemporaryFileWithContent(content=VALID_ACTIONFILE_WITH_TWO_ACTIONS) as action_file:
            content: str = f"""
            api: v0.0.1
            metadata:
              name: test windfile
              description: This is a windfile with no external actions
              author: Test Author
            jobs:
                external-action:
                    use: {action_file.name}
            """
            with TemporaryFileWithContent(content=content) as file:
                merger: Merger = Merger(
                    windfile=None,
                    input_settings=InputSettings(file=file, file_path=file.name),
                    output_settings=self.output_settings,
                    metadata=PassMetadata(),
                )
                windfile: Optional[WindFile] = merger.merge()
                if windfile is None:
                    self.fail("Windfile is None")
                self.assertIsNotNone(windfile)
                self.assertEqual(len(windfile.jobs), 2)

                for name, action_content in [
                    ("external-action_0", 'echo "Hello from a simple action"'),
                    (
                        "external-action_1",
                        'echo "Hello from the second step"\n',
                    ),
                ]:
                    self.assertTrue(name in windfile.jobs)
                    self.assertTrue(isinstance(windfile.jobs[name].root, InternalAction))
                    action: FileAction | InternalAction | PlatformAction | ExternalAction = windfile.jobs[name].root
                    if isinstance(action, InternalAction):
                        self.assertEqual(action.script, action_content)
                    else:
                        self.fail("Action is not an instance of InternalAction, but should be")


if __name__ == "__main__":
    unittest.main()
