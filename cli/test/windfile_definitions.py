# pylint: disable=line-too-long
VALID_WINDFILE_INTERNAL_ACTION: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        jobs:
          internal-action:
            script: echo "This is an internal action"
        """
INVALID_WINDFILE_INTERNAL_ACTION: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        jobs:
          internal-action:
        script: echo "This is an internal action"
        """
VALID_WINDFILE_WITH_NON_EXISTING_ACTIONFILE: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        jobs:
          invalid-action:
            use: ./this-file-does-not-exist.yaml
        """
VALID_WINDFILE_WITH_FILEACTION: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        jobs:
          file-action:
            file: [FILE_ACTION_FILE]
            excludeDuring:
              - working_time
            parameters:
              SORTING_ALGORITHM: quicksort
        """
