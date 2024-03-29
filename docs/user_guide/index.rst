************
Using Aeolus
************

++++++++++++++++++
How do I run this?
++++++++++++++++++

It's easy! Just run the following command:

.. code-block:: bash

    cd cli/
    python3 main.py

or if you prefer docker:

.. code-block:: bash

    docker run --rm -v "./:/tmp" ghcr.io/ls1intum/aeolus/cli:nightly --help

The CLI will guide you through the process of how to generate Bash scripts, Jenkinsfiles, and Bamboo Build Plans.

Let's say you have a windfile, which is our input, with the following content:

.. code-block:: yaml

    api: v0.0.1
    metadata:
      name: example windfile
      id: example-windfile
      description: This is a windfile with an internal action
      author: Andreas Resch
      docker:
        image: ls1tum/artemis-maven-template
        tag: java17-20
    repositories:
      aeolus:
        url: https://github.com/ls1intum/Aeolus.git
        branch: develop
        path: aeolus
    actions:
      - name: script-action
        script: echo "I am a script action"
      - name: template-action
        use: https://github.com/reschandreas/example-action.git
        parameters:
          WHO_TO_GREET: "hello"

Now you simply run the following command:

.. code-block:: bash

    python main.py generate -i windfile.yml -t cli

This will generate a bash script, which looks like this:

.. code-block:: bash

    #!/usr/bin/env bash
    set -e
    export AEOLUS_INITIAL_DIRECTORY=${PWD}
    export REPOSITORY_URL="https://github.com/ls1intum/Aeolus.git"

    scriptaction () {
      echo '⚙️ executing scriptaction'
      echo "I am a script action"
    }

    templateaction_ () {
      local _current_lifecycle="${1}"
      if [[ "${_current_lifecycle}" == "preparation" ]]; then
        echo "⚙️ skipping templateaction_ because it is excluded during preparation"
        return 0
      fi

      echo '⚙️ executing templateaction_'

      export WHO_TO_GREET="hello"
        echo "Hello ${WHO_TO_GREET}"

    }

    main () {
      if [[ "${1}" == "aeolus_sourcing" ]]; then
        return 0 # just source to use the methods in the subshell, no execution
      fi
      local _current_lifecycle="${1}"

      local _script_name
      _script_name=${BASH_SOURCE[0]:-$0}
      cd "${AEOLUS_INITIAL_DIRECTORY}"
      bash -c "source ${_script_name} aeolus_sourcing; scriptaction \"${_current_lifecycle}\""
      cd "${AEOLUS_INITIAL_DIRECTORY}"
      bash -c "source ${_script_name} aeolus_sourcing; templateaction_ \"${_current_lifecycle}\""
    }

    main "${@}"


Now say you want to use Jenkins instead of Bash. You can simply run the following command:

.. code-block:: bash

    python main.py generate -i windfile.yml -t jenkins

This will generate a Jenkinsfile, which looks like this:

.. code-block:: groovy

    pipeline {
      agent {
        docker {
          image 'ls1tum/artemis-maven-template:java17-20'
        }
      }
      parameters {
        string(name: 'current_lifecycle', defaultValue: 'working_time', description: 'The current stage')
      }
      environment {
        REPOSITORY_URL = 'https://github.com/ls1intum/Aeolus.git'
      }

      stages {
        stage('aeolus') {
          steps {
            dir('aeolus') {
              checkout([$class: 'GitSCM',
                branches: [[name: 'develop']],
                doGenerateSubmoduleConfigurations: false,
                userRemoteConfigs: [[
                  name: 'aeolus',
                  url: "${REPOSITORY_URL}"
                ]]
              ])
            }
          }
        }
        stage('script-action') {
          steps {
            sh '''#!/usr/bin/env bash
              echo "I am a script action"
            '''
          }
        }
        stage('template-action_0') {
          when {
            allOf {
                expression { params.current_lifecycle != 'preparation' }
            }
          }
          environment {
            WHO_TO_GREET = 'hello'
          }
          steps {
            sh '''#!/usr/bin/env bash
              echo "Hello ${WHO_TO_GREET}"

            '''
          }
        }
      }
    }


Or if you want to use Bamboo, you can run the following command:

.. code-block:: bash

    python main.py generate -i windfile.yml -t bamboo

This will generate a Bamboo Build Plan, which YAML specs look like this:

.. code-block:: yaml

    --- !!com.atlassian.bamboo.specs.util.BambooSpecProperties
    rootEntity: !!com.atlassian.bamboo.specs.api.model.plan.PlanProperties
      description: This is a windfile with an internal action
      enabled: true
      key:
        key: WINDFILE
      name: windfile
      oid: null
      pluginConfigurations:
      - !!com.atlassian.bamboo.specs.api.model.plan.configuration.ConcurrentBuildsProperties
        maximumNumberOfConcurrentBuilds: 1
        useSystemWideDefault: true
      dependenciesProperties:
        childPlans: []
        dependenciesConfigurationProperties:
          blockingStrategy: NONE
          enabledForBranches: true
          requireAllStagesPassing: false
      labels: []
      notifications: []
      planBranchConfiguration: null
      planBranchManagementProperties:
        branchIntegrationProperties:
          enabled: false
          gatekeeper: false
          integrationBranch: null
          pushOn: false
        createPlanBranch:
          matchingPattern: null
          trigger: MANUAL
        defaultTrigger: null
        deletePlanBranch:
          removeDeletedFromRepository: false
          removeDeletedFromRepositoryPeriod: !!java.time.Duration 'PT168H'
          removeInactiveInRepository: false
          removeInactiveInRepositoryPeriod: !!java.time.Duration 'PT720H'
        issueLinkingEnabled: true
        notificationStrategy: NOTIFY_COMMITTERS
        triggeringOption: INHERITED
      project:
        description: |-
          This is a windfile with an internal action
          ---created using aeolus
        key:
          key: EXAMPLE
        name: example windfile
        oid: null
        repositories: []
        repositoryStoredSpecsData: null
        sharedCredentials: []
        variables: []
      repositories:
      - repositoryDefinition: !!com.atlassian.bamboo.specs.model.repository.git.GitRepositoryProperties
          description: null
          name: aeolus
          oid: null
          parent: null
          project: null
          repositoryViewerProperties: null
          authenticationProperties: null
          branch: develop
          commandTimeout: !!java.time.Duration 'PT3H'
          fetchWholeRepository: false
          sshKeyAppliesToSubmodules: false
          url: https://github.com/ls1intum/Aeolus.git
          useLfs: false
          useRemoteAgentCache: false
          useShallowClones: true
          useSubmodules: false
          vcsChangeDetection:
            changesetFilterPatternRegex: null
            commitIsolationEnabled: false
            configuration: {}
            filterFilePatternOption: NONE
            filterFilePatternRegex: null
            maxRetries: 5
            quietPeriod: !!java.time.Duration 'PT10S'
            quietPeriodEnabled: false
          verboseLogs: false
      repositoryBranches: []
      repositoryStoredSpecsData: null
      stages:
      - description: ''
        finalStage: false
        jobs:
        - description: ''
          enabled: true
          key:
            key: JOB1
          name: Default Job
          oid: null
          pluginConfigurations: []
          artifactSubscriptions: []
          artifacts: []
          cleanWorkingDirectory: false
          dockerConfiguration:
            dockerRunArguments: []
            enabled: true
            image: ls1tum/artemis-maven-template:java17-20
            volumes:
              ${bamboo.working.directory}: ${bamboo.working.directory}
              ${bamboo.tmp.directory}: ${bamboo.tmp.directory}
          finalTasks: []
          requirements: []
          tasks:
          - !!com.atlassian.bamboo.specs.model.task.VcsCheckoutTaskProperties
            conditions: []
            description: Checkout Default Repository
            enabled: true
            requirements: []
            checkoutItems:
            - defaultRepository: false
              path: aeolus
              repository:
                name: aeolus
                oid: null
            cleanCheckout: true
          - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
            conditions: []
            description: script-action
            enabled: true
            requirements: []
            argument: null
            body: |-
              #!/usr/bin/env bash
              echo "I am a script action"
            environmentVariables: null
            interpreter: SHELL
            location: INLINE
            path: null
            workingSubdirectory: null
          - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
            conditions: []
            description: dummy task to prevent wrong result of build plan run
            enabled: true
            requirements: []
            argument: null
            body: echo "⚙️ Executing template-action_0 if stage is correct"
            environmentVariables: null
            interpreter: SHELL
            location: INLINE
            path: null
            workingSubdirectory: null
          - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
            conditions:
            - !!com.atlassian.bamboo.specs.api.model.plan.condition.AnyConditionProperties
              atlassianPlugin:
                completeModuleKey: com.atlassian.bamboo.plugins.bamboo-conditional-tasks:variableCondition
              configuration:
                variable: lifecycle_stage
                operation: matches
                value: ^.*[^(preparation)].*
            description: template-action_0
            enabled: true
            requirements: []
            argument: null
            body: |
              #!/usr/bin/env bash
              echo "Hello ${WHO_TO_GREET}"
            environmentVariables: WHO_TO_GREET=hello
            interpreter: SHELL
            location: INLINE
            path: null
            workingSubdirectory: null
        manualStage: false
        name: Default Stage
      triggers: []
      variables:
      - createOnly: false
        name: lifecycle_stage
        value: working_time
    specModelVersion: 9.4.2
    ...
