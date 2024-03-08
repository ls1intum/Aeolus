***
CLI
***

Aeolus can generate scripts that can be used to automate the deployment of a project. The script is generated based on
the input, the windfile.

++++++++++++++++++++++++++
What does Aeolus generate?
++++++++++++++++++++++++++

Aeolus generates a bash script using best practices to provide a similar workflow to Jenkins and Bamboo. To ensure that
each action is executed in the correct order, the script is divided into functions. Each function contains the commands
of a single defined action and is called in the `main` function.

+++++++++++++++++++++++
Structure of the script
+++++++++++++++++++++++

To ensure that the script is executed correctly, Aeolus uses the `set -e` command to stop the execution of the script if
commands fail. This is useful to avoid the execution of the next commands if the previous ones failed. Aeolus also offers
the possibility to define actions that always need to be executed, regardless of the result of the previous commands.
For this we use the `trap` command that captures the exit signal and executes the defined action. To also ensure that
an `exit` command within an action does not break the script, we source the script instead of executing it and then execute
the `main` function which spawns a subshell for each action.

One example of the script structure is shown below:

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