*****
Setup
*****

Aeolus is implemented using different components, each of which is responsible for a specific part of the system. The main components, structured by their language, are:

* **Python**: The main language used for the generation.

  * **API**: The main entry point for all interactions with Aeolus. It is used to generate and translate the CI configuration files, and to trigger the CI jobs.
  * **CLI**: Using the same code base as the API, the CLI is a command line tool that allows users to interact with Aeolus from the command line.

* **TypeScript**: The language used for the web interface.

  * **Aeolus Playground**: A web interface that allows users to interact with Aeolus from a web browser, without the need to install any software.

* **Java**: The language used for the Bamboo generator.

  * **Bamboo Generator**: A tool that generates the Bamboo configuration files from the CI configuration files.

