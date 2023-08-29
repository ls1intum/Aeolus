import logging
import tempfile
import unittest
from typing import Optional

from classes.generated.definitions import InternalAction
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.merger import Merger
from classes.metadata import PassMetadata
from classes.output_settings import OutputSettings


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
        content: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        jobs:
          internal-action:
            script: echo "This is an internal action"
        """
        with tempfile.NamedTemporaryFile(mode="w+") as file:
            file.write(content)
            file.seek(0)
            print(file.name)
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
        content: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        jobs:
          internal-action:
        script: echo "This is an internal action"
        """
        with tempfile.NamedTemporaryFile(mode="w+") as file:
            file.write(content)
            file.seek(0)
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=OutputSettings(),
                metadata=PassMetadata(),
            )
            windfile = merger.merge()
            self.assertIsNone(windfile)


    def test_merging_nonexisting_file(self):
        content: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        jobs:
          invalid-action:
            use: ./this-file-does-not-exist.yaml
        """
        with tempfile.NamedTemporaryFile(mode="w+") as file:
            file.write(content)
            file.seek(0)
            merger: Merger = Merger(
                windfile=None,
                input_settings=InputSettings(file=file, file_path=file.name),
                output_settings=OutputSettings(),
                metadata=PassMetadata(),
            )
            windfile = merger.merge()
            self.assertIsNone(windfile)


    def test_merge_with_external_actions(self):
        action_file_content: str = """
        api: v0.0.1
        metadata:
          name: simple action
          description: This is an action with a simple script
          author:
            name: Action Author
            email: action@author.com
        steps:
          hello-world:
            script: echo "Hello from a simple action"
          second-step:
            script: |
              echo "Hello from the second step"
        """
        with tempfile.NamedTemporaryFile(mode="w+") as action_file:
            action_file.write(action_file_content)
            action_file.seek(0)

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

            with tempfile.NamedTemporaryFile(mode="w+") as file:
                file.write(content)
                file.seek(0)
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
