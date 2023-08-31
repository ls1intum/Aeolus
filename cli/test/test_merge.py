import logging
import unittest
from typing import Optional

from classes.generated.definitions import InternalAction
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.metadata import PassMetadata
from classes.output_settings import OutputSettings
from test.actionfile_definitions import VALID_ACTIONFILE_WITH_TWO_ACTIONS
from test.testutils import TemporaryFileWithContent
from test.windfile_definitions import (
    VALID_WINDFILE_INTERNAL_ACTION,
    INVALID_WINDFILE_INTERNAL_ACTION,
    VALID_WINDFILE_WITH_NON_EXISTING_ACTIONFILE,
)


class MergeTests(unittest.TestCase):
    output_settings: OutputSettings

    def setUp(self) -> None:
        logging.basicConfig(
            encoding="utf-8", level=logging.DEBUG, format="%(message)s"
        )
        self.output_settings = OutputSettings(
            verbose=True, debug=True, emoji=True
        )

    def test_merge_no_external_actions(self):
        with TemporaryFileWithContent(
            content=VALID_WINDFILE_INTERNAL_ACTION
        ) as file:
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=OutputSettings(),
                metadata=PassMetadata(),
            )
            windfile = merger.merge()
            self.assertEqual(len(windfile.jobs), 1)
            self.assertTrue("internal-action" in windfile.jobs)
            self.assertTrue(
                isinstance(
                    windfile.jobs["internal-action"].root, InternalAction
                )
            )
            action: InternalAction = windfile.jobs["internal-action"].root
            self.assertEqual(
                action.script, 'echo "This is an internal action"'
            )

    def test_merging_invalid_file(self):
        with TemporaryFileWithContent(
            content=INVALID_WINDFILE_INTERNAL_ACTION
        ) as file:
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=OutputSettings(),
                metadata=PassMetadata(),
            )
            windfile = merger.merge()
            self.assertIsNone(windfile)

    def test_merging_nonexisting_file(self):
        with TemporaryFileWithContent(
            content=VALID_WINDFILE_WITH_NON_EXISTING_ACTIONFILE
        ) as file:
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=OutputSettings(),
                metadata=PassMetadata(),
            )
            windfile = merger.merge()
            self.assertIsNone(windfile)

    def test_merge_with_external_actions(self):
        with TemporaryFileWithContent(
            content=VALID_ACTIONFILE_WITH_TWO_ACTIONS
        ) as action_file:
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
                    input_settings=InputSettings(
                        file=file, file_path=file.name
                    ),
                    output_settings=self.output_settings,
                    metadata=PassMetadata(),
                )
                windfile: Optional[WindFile] = merger.merge()
                self.assertTrue(windfile)
                self.assertEqual(len(windfile.jobs), 2)

                for actionname, action_content in [
                    ("external-action_0", 'echo "Hello from a simple action"'),
                    (
                        "external-action_1",
                        'echo "Hello from the second step"\n',
                    ),
                ]:
                    self.assertTrue(actionname in windfile.jobs)
                    self.assertTrue(
                        isinstance(
                            windfile.jobs[actionname].root, InternalAction
                        )
                    )
                    action: InternalAction = windfile.jobs[actionname].root
                    self.assertEqual(action.script, action_content)


if __name__ == "__main__":
    unittest.main()
