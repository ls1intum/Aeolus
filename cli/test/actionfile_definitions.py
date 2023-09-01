# pylint: disable=line-too-long
VALID_ACTIONFILE_WITH_TWO_ACTIONS: str = """
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
INVALID_ACTIONFILE_WITH_ONE_ACTION: str = """
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
        """
