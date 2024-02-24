.. aeolus documentation master file, created by
   sphinx-quickstart on Mon Feb 12 12:41:15 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the documentation of aeolus!
=======================================

Aeolus is a Domain Specific Language (DSL) for defining continuous integration (CI) jobs in a declarative way.
It is designed to be easy to use and to be able to define CI jobs for programming exercises that can be run on different CI platforms.

.. toctree::
   :maxdepth: 3
   :caption: User Guide

   user_guide/index

.. toctree::
   :maxdepth: 3
   :caption: Setup Guide

   setup/index

Features
--------

Currently, Aeolus can generate CI jobs for the following platforms:
 - Bamboo
 - Jenkins
 - Bash Scripts (CLI)

All three systems can be used with the same Aeolus configuration file, which makes it easy to switch between different CI platforms.
The how and why we generate what we generate, is explained in the different target platform sections, see :ref:`targets`.
An example for such a configuration file, we call in Windfile, looks like this:

.. code-block:: yaml
   :caption: Windfile that defines a simple CI job using Aeolus
   :name: example-windfile

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
       environment:
         HELLO: "world"

With this single configuration, we generate the following CI jobs:

***
CLI
***

.. code-block:: sh
   :caption: Bash script generated from the example windfile
   :name: example-bash-script

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

     export HELLO="world"
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


*******
Jenkins
*******

.. code-block:: groovy
   :caption: Jenkinsfile generated from the example windfile
   :name: example-jenkinsfile

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
           HELLO = 'world'
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

.. toctree::
   :maxdepth: 3
   :caption: Target Platforms
   :name: targets

   targets/bamboo/index
   targets/jenkins/index
   targets/cli/index



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
