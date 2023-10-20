import logging
import os
import unittest
from tempfile import NamedTemporaryFile
from typing import Optional

from test.actionfile_definitions import VALID_ACTIONFILE_WITH_TWO_ACTIONS
from test.windfile_definitions import (
    VALID_WINDFILE_INTERNAL_ACTION,
    INVALID_WINDFILE_INTERNAL_ACTION,
    VALID_WINDFILE_WITH_NON_EXISTING_ACTIONFILE,
    VALID_WINDFILE_WITH_FILEACTION,
)
from classes.generated.definitions import InternalAction, FileAction, PlatformAction, ExternalAction
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.pass_metadata import PassMetadata
from classes.output_settings import OutputSettings
from cli_utils.utils import TemporaryFileWithContent


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
            self.assertEqual(len(windfile.actions), 1)
            self.assertTrue("internal-action" in windfile.actions)
            self.assertTrue(isinstance(windfile.actions["internal-action"].root, InternalAction))
            if isinstance(windfile.actions["internal-action"].root, InternalAction):
                action: InternalAction = windfile.actions["internal-action"].root
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
            actions:
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
                self.assertEqual(len(windfile.actions), 2)

                for name, action_content in [
                    ("external-action_0", 'echo "Hello from a simple action"'),
                    (
                        "external-action_1",
                        'echo "Hello from the second step"\n',
                    ),
                ]:
                    self.assertTrue(name in windfile.actions)
                    self.assertTrue(isinstance(windfile.actions[name].root, InternalAction))
                    action: FileAction | InternalAction | PlatformAction | ExternalAction = windfile.actions[name].root
                    if isinstance(action, InternalAction):
                        self.assertEqual(action.script, action_content)
                    else:
                        self.fail("Action is not an instance of InternalAction, but should be")

    def test_merge_with_file_action(self) -> None:
        with NamedTemporaryFile(delete=False) as bash_file:
            content: str = """
            #!/usr/bin/env bash
            for i in $(seq 1 10); do
                echo "Hello $i"
            done
            """
            bash_file.write(content.encode())
            bash_file.flush()
            bash_file.seek(0)
            with TemporaryFileWithContent(
                content=VALID_WINDFILE_WITH_FILEACTION.replace("[FILE_ACTION_FILE]", bash_file.name)
            ) as windfile_file:
                windfile_file.seek(0)
                merger: Merger = Merger(
                    windfile=None,
                    input_settings=InputSettings(file=windfile_file, file_path=windfile_file.name),
                    output_settings=self.output_settings,
                    metadata=PassMetadata(),
                )
                windfile: Optional[WindFile] = merger.merge()
                if windfile is None:
                    os.unlink(bash_file.name)
                    self.fail("Windfile is None")
                self.assertIsNotNone(windfile)
                self.assertEqual(len(windfile.actions), 1)
                self.assertTrue("file-action_0" in windfile.actions)
                self.assertTrue(isinstance(windfile.actions["file-action_0"].root, InternalAction))
                action: FileAction | InternalAction | PlatformAction | ExternalAction = windfile.actions[
                    "file-action_0"
                ].root
                if isinstance(action, InternalAction):
                    self.assertEqual(action.script, content)
                    if action.excludeDuring is None:
                        self.fail("Action excludeDuring is None, but should not be")
                    self.assertTrue("working_time" in [e.name for e in action.excludeDuring])
                    if action.parameters is None:
                        self.fail("Action parameters are None, but should not be")
                    self.assertIsNotNone(action.parameters)
                    self.assertIsNotNone(action.parameters.root)
                    self.assertIsNotNone(action.parameters.root.root)
                    self.assertTrue("SORTING_ALGORITHM" in action.parameters.root.root)
                else:
                    self.fail("Action is not an instance of InternalAction, but should be")
        os.unlink(bash_file.name)


if __name__ == "__main__":
    unittest.main()
