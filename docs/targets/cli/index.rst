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