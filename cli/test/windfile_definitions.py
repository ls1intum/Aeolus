# pylint: disable=line-too-long
VALID_WINDFILE_INTERNAL_ACTION: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        actions:
          - name: internal-action
            script: echo "This is an internal action"
        """
INVALID_WINDFILE_INTERNAL_ACTION: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        actions:
          internal-action:
        script: echo "This is an internal action"
        """
VALID_WINDFILE_WITH_NON_EXISTING_ACTIONFILE: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        actions:
          - name: invalid-action
            use: ./this-file-does-not-exist.yaml
        """
VALID_WINDFILE_WITH_FILEACTION: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        actions:
          - name: file-action
            file: [FILE_ACTION_FILE]
            excludeDuring:
              - working_time
            parameters:
              SORTING_ALGORITHM: quicksort
        """
VALID_WINDFILE_WITH_ENV_VARIABLES_AND_DOCKER: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          id: test-windfile
          description: This is a windfile with no external actions
          author: Test Author
          docker:
            image: ls1tum/artemis-maven-template
            tag: java17-20
            volumes:
              - ${WORKDIR}:/aeolus
            parameters:
              - --cpus
              - '"2"'
              - --memory
              - '"2g"'
              - --memory-swap
              - '"2g"'
              - --pids-limit
              - '"1000"'
        actions:
          - name: internal-action
            script: |
                echo "This is an internal action and it uses an environment variable: $WORKDIR"
          - name: second-action
            script: |
                echo "This is the second action and it uses an environment variable: ${TMPDIR}"
            parameters:
              RUNNER: $RUNNER_NAME
        """

VALID_WINDFILE_WITH_MULTIPLE_DOCKER: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
          docker:
            image: ls1tum/artemis-maven-template
            tag: java17-20
            volumes:
              - ${WORKDIR}:/aeolus
            parameters:
              - --cpus
              - '"2"'
              - --memory
              - '"2g"'
              - --memory-swap
              - '"2g"'
              - --pids-limit
              - '"1000"'
        actions:
          - name: internal-action
            docker:
              image: ls1tum/artemis-maven-template
              tag: java19-20
            script: echo "This is an internal action and in docker"
          - name: second-action
            docker:
              image: ls1tum/artemis-c-template:nightly
            script: echo "This is the second action and in another docker"
        """

VALID_WINDFILE_WITH_MULTIPLE_REPOSITORIES: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
          docker:
            image: ls1tum/artemis-maven-template
            tag: java17-20
            volumes:
              - ${WORKDIR}:/aeolus
            parameters:
              - --cpus
              - '"2"'
              - --memory
              - '"2g"'
              - --memory-swap
              - '"2g"'
              - --pids-limit
              - '"1000"'
        repositories:
          aeolus:
            url: https://github.com/ls1intum/Aeolus.git
            branch: develop
            path: aeolus
          aeolus1:
            url: https://github.com/ls1intum/Aeolus1.git
            branch: develop
            path: aeolus1
        actions:
          - name: internal-action
            docker:
              image: ls1tum/artemis-maven-template
              tag: java19-20
            script: echo "This is an internal action and in docker"
          - name: second-action
            docker:
              image: ls1tum/artemis-c-template:nightly
            script: echo "This is the second action and in another docker"
        """

WINDFILE_WITH_ALWAYS_ACTION: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        actions:
          - name: internal-action
            script: echo "This is an internal action"
          - name: always-action
            script: echo "This is an internal action"
            runAlways: true
        """

WINDFILE_WITH_WORKDIR_ACTION: str = """
        api: v0.0.1
        metadata:
          name: test windfile
          description: This is a windfile with no external actions
          author: Test Author
        actions:
          - name: internal-action
            workdir: /aeolus
            script: echo "This is an internal action in a special directory"
          - name: always-action
            script: echo "This is an internal action"
            runAlways: true
        """
