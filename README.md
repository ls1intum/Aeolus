# Aeolus: A Domain-Specific Language for Streamlining CI Job Configuration for Programming Exercises

![tests](https://github.com/ls1intum/Aeolus/actions/workflows/docs.yaml/badge.svg)
![tests](https://github.com/ls1intum/Aeolus/actions/workflows/python-unit-tests.yaml/badge.svg)
![coverage](https://ls1intum.github.io/Aeolus/_images/coverage.svg)
![containers](https://github.com/ls1intum/Aeolus/actions/workflows/build-and-push.yaml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

On how to use Aeolus, please refer to the [documentation](https://ls1intum.github.io/Aeolus/).

Aeolus is a complementary tool to Artemis, the online platform for programming exercises. It is a domain-specific language
for streamlining the configuration of continuous integration (CI) jobs for programming exercises. Aeolus provides a
standard definition that is able to generate code for several targets, such as CLI, Jenkins, and Bamboo. This allows
instructors to create custom CI jobs for their programming exercises without having to rewrite the configuration for
each platform.

## Why?

In the context of programming exercises, it is common to have a set of CI jobs that are executed for each student
submission. These jobs typically include tasks such as compiling the code, running tests, and generating test results. In
addition, there are often platform-specific tasks, such as setting up the environment, that need to be executed before

## How?

The idea is to define an input language, parse, and validate it and generate the CI configuration
for multiple platforms (e.g. CLI, Bamboo, Jenkins, ...). And therefore be able to
switch the CI platform without having to rewrite the configuration.

## Development

The system is still under development but already ready for use. We plan on supporting the following platforms:

- CLI
- Jenkins
- Bamboo

For now, we generate the jobs/build plans/scripts in the respective platform's language from two
different input files, one for the set of jobs to be executed (called Windfile) and importable, reusable
and shareable modular actionfiles.

A windfile looks like this:

```yaml
api: v0.0.1
metadata:
  name: example windfile
  id: example-windfile
  description: This is a windfile with an internal action
  author: Andreas Resch
  docker:
    image: ls1tum/artemis-maven-template
    tag: java17-20
    volumes:
      - ${WORKDIR}:/aeolus
  gitCredentials: artemis_gitlab_admin_credentials
repositories:
  aeolus:
    url: https://github.com/ls1intum/Aeolus.git
    branch: develop
    path: aeolus
actions:
  - name: set-java-container
    script: set
  - name: set-c-container
    docker:
      image: ghcr.io/ls1intum/artemis-c-docker
    script: set
  - name: internal-action
    script: |
      echo "This is an internal action"
  - name: external-action
    use: simple-action.yml
    excludeDuring:
      - working_time
  - name: clean_up
    script: |
      rm -rf aeolus/
    runAlways: true
```

An actionfile looks like this:

```yaml
api: v0.0.1
metadata:
  name: simple action
  description: This is an action with a simple script
  author:
    name: Andreas Resch
    email: andreas@resch.io
steps:
  - name: hello-world
    parameters:
      WHO_TO_GREET: "world"
    excludeDuring:
      - preparation
    script: |
      echo "Hello ${WHO_TO_GREET}"
```

The generated CLI script for the above example would look like this:

`python main.py -dev generate -t cli -i windfile.yaml`
<!---
Generate with python main.py -dev generate -t cli -i examples/example-windfile-readme.yml
--->

```bash
#!/usr/bin/env bash
set -e
export AEOLUS_INITIAL_DIRECTORY=${PWD}
export REPOSITORY_URL="https://github.com/ls1intum/Aeolus.git"

setjavacontainer () {
  echo '⚙️ executing setjavacontainer'
  set
}

setccontainer () {
  echo '⚙️ executing setccontainer'
  set
}

internalaction () {
  echo '⚙️ executing internalaction'
  echo "This is an internal action"

}

externalaction_ () {
  local _current_lifecycle="${1}"
  if [[ "${_current_lifecycle}" == "working_time" ]]; then
    echo "⚙️ skipping externalaction_ because it is excluded during working_time"
    return 0
  fi
  
  if [[ "${_current_lifecycle}" == "preparation" ]]; then
    echo "⚙️ skipping externalaction_ because it is excluded during preparation"
    return 0
  fi
  
  echo '⚙️ executing externalaction_'
  
  export WHO_TO_GREET="world"
    echo "Hello ${WHO_TO_GREET}"
}

clean_up () {
  echo '⚙️ executing clean_up'
  rm -rf aeolus/

}

final_aeolus_post_action () {
  set +e # from now on, we don't exit on errors
  echo '⚙️ executing final_aeolus_post_action'
  cd "${AEOLUS_INITIAL_DIRECTORY}"
  clean_up "${_current_lifecycle}"
}

main () {
  if [[ "${1}" == "aeolus_sourcing" ]]; then
    return 0 # just source to use the methods in the subshell, no execution
  fi
  local _current_lifecycle="${1}"

  local _script_name
  _script_name=${BASH_SOURCE[0]:-$0}
  trap final_aeolus_post_action EXIT

  cd "${AEOLUS_INITIAL_DIRECTORY}"
  bash -c "source ${_script_name} aeolus_sourcing; setjavacontainer \"${_current_lifecycle}\""
  cd "${AEOLUS_INITIAL_DIRECTORY}"
  bash -c "source ${_script_name} aeolus_sourcing; setccontainer \"${_current_lifecycle}\""
  cd "${AEOLUS_INITIAL_DIRECTORY}"
  bash -c "source ${_script_name} aeolus_sourcing; internalaction \"${_current_lifecycle}\""
  cd "${AEOLUS_INITIAL_DIRECTORY}"
  bash -c "source ${_script_name} aeolus_sourcing; externalaction_ \"${_current_lifecycle}\""
}

main "${@}"
```

And the generated Jenkinsfile would look like this:

`python main.py -dev generate -t jenkins -i windfile.yaml`

```groovy
pipeline {
  agent {
    docker {
      image 'ls1tum/artemis-maven-template:java17-20'
      args '-v ${PWD}:/aeolus '
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
                                                credentialsId: 'artemis_gitlab_admin_credentials',
                                                name: 'aeolus',
                                                url: "${REPOSITORY_URL}"
                                        ]]
          ])
        }
      }
    }
    stage('set-java-container') {
      agent {
        docker {
          image 'ls1tum/artemis-maven-template:java17-20'
        }
      }
      steps {
        sh '''
          set
        '''
      }
    }
    stage('set-c-container') {
      agent {
        docker {
          image 'ghcr.io/ls1intum/artemis-c-docker:latest'
        }
      }
      steps {
        sh '''
          set
        '''
      }
    }
    stage('internal-action') {
      agent {
        docker {
          image 'ls1tum/artemis-maven-template:java17-20'
        }
      }
      steps {
        sh '''
          echo "This is an internal action"

        '''
      }
    }
    stage('external-action_0') {
      agent {
        docker {
          image 'ls1tum/artemis-maven-template:java17-20'
        }
      }
      when {
        allOf {
          expression { params.current_lifecycle != 'working_time' }
          expression { params.current_lifecycle != 'preparation' }
        }
      }
      environment {
        WHO_TO_GREET = 'world'
      }
      steps {
        sh '''
          echo "Hello ${WHO_TO_GREET}"
        '''
      }
    }
  }
  post {
    always {
      sh '''
    rm -rf aeolus/

    '''
      cleanWs()
    }
  }
}
```

And the generated Bamboo YAML specs would look like this:

`python main.py -dev generate -t bamboo -i windfile.yaml`

```yaml
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
        authenticationProperties: !!com.atlassian.bamboo.specs.model.repository.git.SharedCredentialsAuthenticationProperties
          sharedCredentials:
            name: artemis_gitlab_admin_credentials
            oid: null
            scope: GLOBAL
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
            key: CHECKOUT1
          name: Checkout
          oid: null
          pluginConfigurations: []
          artifactSubscriptions: []
          artifacts: []
          cleanWorkingDirectory: false
          dockerConfiguration:
            dockerRunArguments: []
            enabled: false
            image: null
            volumes: {}
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
      manualStage: false
      name: Checkout
    - description: ''
      finalStage: false
      jobs:
        - description: ''
          enabled: true
          key:
            key: SETJAVACONTAINER1
          name: set-java-container
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
              ${bamboo.working.directory}: /aeolus
              ${bamboo.tmp.directory}: ${bamboo.tmp.directory}
          finalTasks: []
          requirements: []
          tasks:
            - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
              conditions: []
              description: set-java-container
              enabled: true
              requirements: []
              argument: null
              body: set
              environmentVariables: null
              interpreter: SHELL
              location: INLINE
              path: null
              workingSubdirectory: null
      manualStage: false
      name: setjavacontainer
    - description: ''
      finalStage: false
      jobs:
        - description: ''
          enabled: true
          key:
            key: SETCCONTAINER2
          name: set-c-container
          oid: null
          pluginConfigurations: []
          artifactSubscriptions: []
          artifacts: []
          cleanWorkingDirectory: false
          dockerConfiguration:
            dockerRunArguments: []
            enabled: true
            image: ghcr.io/ls1intum/artemis-c-docker:latest
            volumes:
              ${bamboo.working.directory}: ${bamboo.working.directory}
              ${bamboo.tmp.directory}: ${bamboo.tmp.directory}
          finalTasks: []
          requirements: []
          tasks:
            - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
              conditions: []
              description: set-c-container
              enabled: true
              requirements: []
              argument: null
              body: set
              environmentVariables: null
              interpreter: SHELL
              location: INLINE
              path: null
              workingSubdirectory: null
      manualStage: false
      name: setccontainer
    - description: ''
      finalStage: false
      jobs:
        - description: ''
          enabled: true
          key:
            key: INTERNALACTION3
          name: internal-action
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
              ${bamboo.working.directory}: /aeolus
              ${bamboo.tmp.directory}: ${bamboo.tmp.directory}
          finalTasks: []
          requirements: []
          tasks:
            - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
              conditions: []
              description: internal-action
              enabled: true
              requirements: []
              argument: null
              body: |
                echo "This is an internal action"
              environmentVariables: null
              interpreter: SHELL
              location: INLINE
              path: null
              workingSubdirectory: null
      manualStage: false
      name: internalaction
    - description: ''
      finalStage: false
      jobs:
        - description: ''
          enabled: true
          key:
            key: EXTERNALACTION04
          name: external-action_0
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
              ${bamboo.working.directory}: /aeolus
              ${bamboo.tmp.directory}: ${bamboo.tmp.directory}
          finalTasks: []
          requirements: []
          tasks:
            - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
              conditions: []
              description: dummy task to prevent wrong result of build plan run
              enabled: true
              requirements: []
              argument: null
              body: echo "⚙️ Executing external-action_0 if stage is correct"
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
                    value: ^.*[^(preparation)][^(working_time)].*
              description: external-action_0
              enabled: true
              requirements: []
              argument: null
              body: echo "Hello ${WHO_TO_GREET}"
              environmentVariables: WHO_TO_GREET=world
              interpreter: SHELL
              location: INLINE
              path: null
              workingSubdirectory: null
      manualStage: false
      name: externalaction0
    - description: ''
      finalStage: false
      jobs:
        - description: ''
          enabled: true
          key:
            key: CLEANUP5
          name: clean_up
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
              ${bamboo.working.directory}: /aeolus
              ${bamboo.tmp.directory}: ${bamboo.tmp.directory}
          finalTasks:
            - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
              conditions: []
              description: clean_up
              enabled: true
              requirements: []
              argument: null
              body: |
                rm -rf aeolus/
              environmentVariables: null
              interpreter: SHELL
              location: INLINE
              path: null
              workingSubdirectory: null
          requirements: []
          tasks: []
      manualStage: false
      name: cleanup
  triggers: []
  variables:
    - createOnly: false
      name: lifecycle_stage
      value: working_time
specModelVersion: 9.4.2
...
```

# Features

### Windfile

The windfile is the main input file for the Aeolus system. It contains the configuration for the CI jobs and references
to actionfiles.
The yaml specification for the windfile can be found [here](schemas/v0.0.1/schemas/windfile.json).

In a windfile, you can define jobs of different types. Currently, there are four types of jobs:

- `script`: A job that is defined in the windfile itself

```yaml
  - name: script-action
    script: |
      echo "This is an internal action"
```

- `external`: A job that is defined in an actionfile

```yaml
  - name: external-action
    use: simple-action.yml
```

- `file`: A job that includes a file e.g. a bash script

```yaml
  - name: file-action
    file: file-action.sh
```

- `platform`: A job that includes a platform-specific script, used to prepare the CI system for the eventual execution
  of the other jobs
  or platform specific actions. The example shown below is translated into a TestParser task in Bamboo which
  parses the test results of the other actions, this is only needed in Bamboo.

```yaml
  - name: platform-action
    parameters:
      ignore_time: false
      test_results: '**/test-results/test/*.xml'
    platform: bamboo
    kind: junit
    runAlways: true
```

Every type of job can have the following properties:

- `excludeDuring`: A list of lifecycles during which the job should be excluded from execution,
  possible options are:
    - `preparation`
    - `working_time`
    - `post_deadline`
    - `evaluation`
    - `all`

### Code Generation

| Feature                        | CLI/Bash | Jenkins | Bamboo |
|--------------------------------|:--------:|:-------:|:------:|
| simple script generation       |    ✅     |    ✅    |   ✅    |
| usage of environment variables |    ✅     |    ✅    |   ✅    |
| lifecycle parameter            |    ✅     |    ✅    |   ✅    |

### Additional Features

| Feature                      | CLI/Bash | Jenkins | Bamboo |
|------------------------------|:--------:|:-------:|:------:|
| build trigger                |    ✅     |    ✅    |   ✅    |
| single docker image          |    ✅     |    ✅    |   ✅    |
| multiple docker images       |    ❌     |    ✅    |   ✅    |
| translating back to Aeolus   |    ❌     |    ❌    |   ✅    |
| publishing results/artifacts |    ✅     |    ✅    |   ✅    |


## Translating back to Aeolus

If you have build plans in Bamboo and want to migrate away, or simply edit these plans, aeolus can help you.
You can use the `translate` command to translate a build plan into a windfile. This windfile can then be used to
generate the build plan again, or to edit it and generate a new build plan.

To be able to translate a build plan, you need access to it's definition using an access token. You can create an
access token in Bamboo under `Profile` -> `Personal access tokens`. You can then use this token to translate the build plan
with the CLI tool using the following command:

```
python main.py translate -k <bamboo-build-plan-key> --url <bamboo-url> -t <bamboo-token>
```
The tool will connect to bamboo, retrieve the build plan and translate it into a windfile. The windfile will be printed to stdout.

## Contributors

<a href="https://github.com/ls1intum/Aeolus/graphs/contributors">
  <img src="https://contributors-img.web.app/image?repo=ls1intum/Aeolus"  alt="contributors"/>
</a>