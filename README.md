# Aeolus: A Domain-Specific Language for Streamlining CI Job Configuration for Programming Exercises

This repository will contain the work of [my](https://github.com/reschandreas) master's thesis. The goal of this thesis is to create a domain-specific language (DSL) for streamlining CI job configuration for programming exercises.

## Why?
Currently, in Artemis, it is tiresome to configure CI jobs that deviate from the standard templates.
Aeolus should help to make the configuration easier, more readable and most importantly more platform-independent.

## How?
The idea is to define an input grammar, parse and validate it and generate the CI configuration 
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
jobs:
  clone:
    use: clone-default
    parameters:
      repository: https://github.com/ls1intum/Aeolus.git
      branch: develop
      path: .
  internal-action:
    script: |
      echo "This is an internal action"
  external-action:
    use: simple-action.yml
    excludeDuring:
      - working_time
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
# step clone
# generated from step clone
# original type was clone-default
clone () {
  echo '🖨️ cloning clone'
  git clone https://github.com/ls1intum/Aeolus.git .
}
# step internal-action
# generated from step internal-action
# original type was internal
internal-action () {
  echo '⚙️  executing internal-action'
  echo "This is an internal action"
}
# step external-action
# generated from step external-action
# original type was internal
external-action () {
  local _current_lifecycle="${1}"
  if [[ "${_current_lifecycle}" == "preparation" ]]; then
    echo '⚠️  external-action is excluded during preparation'
    return 0
  fi
  echo '⚙️  executing external-action'
  WHO_TO_GREET="world"
  echo "Hello ${WHO_TO_GREET}"
}


# main function
main () {
  local _current_lifecycle="${1}"
  clone $_current_lifecycle
  internal-action $_current_lifecycle
  external-action $_current_lifecycle
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
    stage('clone') {
      steps {
        checkout([$class: 'GitSCM',
                  branches: [[name: 'develop']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [],
                  submoduleCfg: [],
                  userRemoteConfigs: [[
                    credentialsId: 'artemis_gitlab_admin_credentials',
                    name: 'clone',
                    url: 'https://github.com/ls1intum/Aeolus.git'
                  ]]
        ])
      }
    }
    // step internal-action
    // generated from step internal-action
    // original type was internal
    stage('internal-action') {
      steps {
        sh '''
         echo "This is an internal action"
        '''
      }
    }
    // step external-action
    // generated from step external-action
    // original type was internal
    stage('external-action') {
      when {
        anyOf {
          expression { params.current_lifecycle != 'preparation' }
        }
      }
      environment {
        WHO_TO_GREET = "world"
      }
      steps {
        sh '''
         echo "Hello ${WHO_TO_GREET}"
        '''
      }
    }
  }
}

```

# Features

### Windfile

The windfile is the main input file for the Aeolus system. It contains the configuration for the CI jobs and references to actionfiles.
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
- `platform`: A job that includes a platform-specific script, used to prepare the CI system for the eventual execution of the other jobs
```yaml
  platform-action:
    platform: jenkins
    script: |
      curl https://<your-jenkins-url>/job/<your-job-name>/build?token=<your-token>
```

Every type of job can have the following properties:
- `excludeDuring`: A list of lifecycles during which the job should be excluded from execution, 
possible options are:
  - `preparation`
  - `working_time`
  - `post_deadline`
  - `evaluation`
  - `always`

### Code Generation

| Feature                        | CLI/Bash |  Jenkins  |  Bamboo  |
|--------------------------------|:--------:|:---------:|:--------:|
| simple script generation       |    ✅     |     ✅     |    ❌     |
| usage of environment variables |    ✅     |     ✅     |    ❌     |
| lifecycle parameter            |    ✅     |     ✅     |    ❌     |
