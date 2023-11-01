# Aeolus: A Domain-Specific Language for Streamlining CI Job Configuration for Programming Exercises

This repository will contain the work of [my](https://github.com/reschandreas) master's thesis. The goal of this thesis
is to create a domain-specific language (DSL) for streamlining CI job configuration for programming exercises.

## Why?

Currently, in Artemis, it is hard to create custom CI jobs. With Aeolus we provide a standard definition that
is able to generate code for several targets.

## How?

The idea is to define an input language, parse and validate it and generate the CI configuration
for multiple platforms (e.g. CLI, Bamboo, Jenkins, ...). And therefore be able to
switch the CI platform without having to rewrite the configuration.

## Development

The system is still under development and not ready for use, yet. We plan on supporting the following platforms:

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
  description: This is a windfile with an internal action
  author: Andreas Resch
  gitCredentials: artemis_gitlab_admin_credentials
repositories:
  aeolus:
    url: https://github.com/ls1intum/Aeolus.git
    branch: develop
    path: aeolus
actions:
  internal-action:
    script: |
      echo "This is an internal action"
  external-action:
    use: simple-action.yml
    excludeDuring:
      - working_time
  clean_up:
    script: |
      rm -rf aeolus/
    run_always: true
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
  hello-world:
    parameters:
      WHO_TO_GREET: "world"
    excludeDuring:
      - preparation
    script: |
      echo "Hello ${WHO_TO_GREET}"
```

The generated CLI script for the above example would look like this:

`python main.py -dev generate -t cli -i windfile.yaml`

```bash
#!/usr/bin/env bash
set -e
# step aeolus
# generated from repository aeolus
clone_aeolus () {
  echo '🖨️ cloning aeolus'
  git clone https://github.com/ls1intum/Aeolus.git --branch develop aeolus
}
# step internal-action
# generated from step internal-action
# original type was internal
internal-action () {
  echo '⚙️ executing internal-action'
  echo "This is an internal action"
}
# step clean_up
# generated from step clean_up
# original type was internal
clean_up () {
  echo '⚙️ executing clean_up'
  rm -rf aeolus/
}
# step external-action_0
# generated from step external-action
# original type was internal
external-action_0 () {
  local _current_lifecycle="${1}"
  if [[ "${_current_lifecycle}" == "working_time" ]]; then
    echo '⚠️  external-action_0 is excluded during working_time'
    return 0
  fi
  if [[ "${_current_lifecycle}" == "preparation" ]]; then
    echo '⚠️  external-action_0 is excluded during preparation'
    return 0
  fi
  echo '⚙️ executing external-action_0'
  WHO_TO_GREET="world"
  echo "Hello ${WHO_TO_GREET}"
}

# always steps
final_aeolus_post_action () {
  echo '⚙️ executing final_aeolus_post_action'
  clean_up $_current_lifecycle
}


# main function
main () {
  local _current_lifecycle="${1}"
  trap final_aeolus_post_action EXIT
  clone_aeolus $_current_lifecycle
  internal-action $_current_lifecycle
  external-action_0 $_current_lifecycle
}

main $@

```

And the generated Jenkinsfile would look like this:

`python main.py -dev generate -t jenkins -i windfile.yaml`

```groovy
pipeline {
    agent any
    parameters {
        string(name: 'current_lifecycle', defaultValue: 'working_time', description: 'The current lifecycle')
    }
    stages {
        stage('aeolus') {
            steps {
                echo '🖨️ cloning aeolus'
                dir('aeolus') {
                    checkout([$class                           : 'GitSCM',
                              branches                         : [[name: 'develop']],
                              doGenerateSubmoduleConfigurations: false,
                              extensions                       : [],
                              submoduleCfg                     : [],
                              userRemoteConfigs                : [[
                                                                          credentialsId: 'artemis_gitlab_admin_credentials',
                                                                          name         : 'aeolus',
                                                                          url          : 'https://github.com/ls1intum/Aeolus.git'
                                                                  ]]
                    ])
                }
            }
        }
        // step internal-action
        // generated from step internal-action
        // original type was internal
        stage('internal-action') {
            steps {
                echo '⚙️ executing internal-action'
                sh '''
         echo "This is an internal action"
        '''
            }
        }
        // step external-action_0
        // generated from step external-action
        // original type was internal
        stage('external-action_0') {
            when {
                anyOf {
                    expression { params.current_lifecycle != 'preparation' }
                    expression { params.current_lifecycle != 'working_time' }
                }
            }
            environment {
                WHO_TO_GREET = "world"
            }
            steps {
                echo '⚙️ executing external-action_0'
                sh '''
         echo "Hello ${WHO_TO_GREET}"
        '''
            }
        }
    }
    post {
        // step clean_up
        // generated from step clean_up
        // original type was internal
        always {
            echo '⚙️ executing clean_up'
            sh '''
         rm -rf aeolus/
        '''
        }
    }
}



```

And the generated Bamboo YAML specs would look like this:

`python main.py -dev generate -t bamboo -i windfile.yaml`

```yaml
--- !!com.atlassian.bamboo.specs.util.BambooSpecProperties
rootEntity: !!com.atlassian.bamboo.specs.api.model.plan.PlanProperties
  description: Plan created from stdin
  enabled: true
  key:
    key: WINDFILE
  name: example windfile
  oid: null
  pluginConfigurations: [ ]
  dependenciesProperties:
    childPlans: [ ]
    dependenciesConfigurationProperties:
      blockingStrategy: NONE
      enabledForBranches: true
      requireAllStagesPassing: false
  labels: [ ]
  notifications: [ ]
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
      removeDeletedFromRepositoryPeriod: !!java.time.Duration 'PT0S'
      removeInactiveInRepository: false
      removeInactiveInRepositoryPeriod: !!java.time.Duration 'PT0S'
    issueLinkingEnabled: true
    notificationStrategy: NONE
    triggeringOption: INHERITED
  project:
    description: |-
      This is a windfile with an internal action
      ---created using aeolus
    key:
      key: EXAMPLE
    name: EXAMPLE
    oid: null
    repositories: [ ]
    repositoryStoredSpecsData: null
    sharedCredentials: [ ]
    variables: [ ]
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
          configuration: { }
          filterFilePatternOption: NONE
          filterFilePatternRegex: null
          maxRetries: 5
          quietPeriod: !!java.time.Duration 'PT10S'
          quietPeriodEnabled: false
        verboseLogs: false
  repositoryBranches: [ ]
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
          pluginConfigurations: [ ]
          artifactSubscriptions: [ ]
          artifacts: [ ]
          cleanWorkingDirectory: false
          dockerConfiguration:
            dockerRunArguments: [ ]
            enabled: false
            image: null
            volumes: { }
          finalTasks: [ ]
          requirements: [ ]
          tasks:
            - !!com.atlassian.bamboo.specs.model.task.VcsCheckoutTaskProperties
              conditions: [ ]
              description: Checkout Default Repository
              enabled: true
              requirements: [ ]
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
            key: INTERNALACTION1
          name: internal-action
          oid: null
          pluginConfigurations: [ ]
          artifactSubscriptions: [ ]
          artifacts: [ ]
          cleanWorkingDirectory: false
          dockerConfiguration:
            dockerRunArguments: [ ]
            enabled: false
            image: null
            volumes: { }
          finalTasks: [ ]
          requirements: [ ]
          tasks:
            - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
              conditions: [ ]
              description: internal-action
              enabled: true
              requirements: [ ]
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
            key: CLEANUP2
          name: clean_up
          oid: null
          pluginConfigurations: [ ]
          artifactSubscriptions: [ ]
          artifacts: [ ]
          cleanWorkingDirectory: false
          dockerConfiguration:
            dockerRunArguments: [ ]
            enabled: false
            image: null
            volumes: { }
          finalTasks: [ ]
          requirements: [ ]
          tasks:
            - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
              conditions: [ ]
              description: clean_up
              enabled: true
              requirements: [ ]
              argument: null
              body: |
                rm -rf aeolus/
              environmentVariables: null
              interpreter: SHELL
              location: INLINE
              path: null
              workingSubdirectory: null
      manualStage: false
      name: cleanup
    - description: ''
      finalStage: false
      jobs:
        - description: ''
          enabled: true
          key:
            key: EXTERNALACTION03
          name: external-action_0
          oid: null
          pluginConfigurations: [ ]
          artifactSubscriptions: [ ]
          artifacts: [ ]
          cleanWorkingDirectory: false
          dockerConfiguration:
            dockerRunArguments: [ ]
            enabled: false
            image: null
            volumes: { }
          finalTasks: [ ]
          requirements: [ ]
          tasks:
            - !!com.atlassian.bamboo.specs.model.task.ScriptTaskProperties
              conditions: [ ]
              description: dummy task to prevent wrong result of build plan run
              enabled: true
              requirements: [ ]
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
                    value: ^.*[^(working_time)][^(preparation)].*
              description: external-action_0
              enabled: true
              requirements: [ ]
              argument: null
              body: echo "Hello ${WHO_TO_GREET}"
              environmentVariables: WHO_TO_GREET=world
              interpreter: SHELL
              location: INLINE
              path: null
              workingSubdirectory: null
      manualStage: false
      name: externalaction0
  triggers: [ ]
  variables:
    - createOnly: false
      name: lifecycle_stage
      value: working_time
specModelVersion: 9.3.3

...
```

# Features

### Windfile

The windfile is the main input file for the Aeolus system. It contains the configuration for the CI jobs and references
to actionfiles.
The yaml specification for the windfile can be found [here](schemas/v0.0.1/schemas/windfile.json).

In a windfile, you can define jobs of different types. Currently, there are four types of jobs:

- `internal`: A job that is defined in the windfile itself

```yaml
  internal-action:
    script: |
      echo "This is an internal action"
```

- `external`: A job that is defined in an actionfile

```yaml
  external-action:
    use: simple-action.yml
```

- `file`: A job that includes a file e.g. a bash script

```yaml
  file-action:
    file: file-action.sh
```

- `platform`: A job that includes a platform-specific script, used to prepare the CI system for the eventual execution
  of the other jobs
  or platform specific actions. The example shown below is translated into a TestParser task in Bamboo which
  parses the test results of the other actions, this is only needed in Bamboo.

```yaml
  platform-action:
    parameters:
      ignore_time: false
      test_results: '**/test-results/test/*.xml'
    platform: bamboo
    kind: junit
    run_always: true
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

| Feature                    | CLI/Bash | Jenkins | Bamboo |
|----------------------------|:--------:|:-------:|:------:|
| build trigger              |    ✅     |    ✅    |   ✅    |
| single docker image        |    ✅     |    ✅    |   ✅    |
| multiple docker images     |    ❌     |    ✅    |   ✅    |
| translating back to Aeolus |    ❌     |    ❌    |   ✅    |


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