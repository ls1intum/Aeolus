+++++++++
Languages
+++++++++

Aeolus is implemented using different components, each of which is responsible for a specific part of the system. The main components, structured by their language, are:

* **Python**: The main language used for the generation.

  * **API**: The main entry point for all interactions with Aeolus. It is used to generate and translate the CI configuration files, and to trigger the CI jobs.
  * **CLI**: Using the same code base as the API, the CLI is a command line tool that allows users to interact with Aeolus from the command line.

* **TypeScript**: The language used for the web interface.

  * **Aeolus Playground**: A web interface that allows users to interact with Aeolus from a web browser, without the need to install any software.

* **Java**: The language used for the Bamboo generator.

  * **Bamboo Generator**: A tool that generates the Bamboo configuration files from the CI configuration files.

+++++++++++++++
Local Dev Setup
+++++++++++++++

To set up a local development environment, you will need to use a virtual environment, we use `venv` with `pip-tools` for this purpose.

To create a virtual environment, follow the official Python documentation: https://docs.python.org/3/library/venv.html

After creating the virtual environment, you can install the dependencies using pip:

.. code-block:: bash

    cd api
    pip install -r requirements.txt

.. code-block:: bash

    cd cli
    pip install -r requirements.txt

After installing the dependencies, you can use the CLI using the following commands:

.. code-block:: bash

    cd cli
    python main.py --help

The cli will guide you through the available commands.
How updating the requirements.txt works, is described in the two files respectively.

To run the API, you can use the following command:

.. code-block:: bash

    cd api
    uvicorn --reload --host 127.0.0.1 --port 8090 main:app --reload

This will start the API on http://127.0.0.1:8090.

To run the Aeolus Playground, you can use the following command:

.. code-block:: bash

    cd playground
    npm install
    npm start

To run the Bamboo Generator, you can use the following command:

.. code-block:: bash

    cd bamboo-generator
    ./gradlew shadowJar --no-daemon -x :generateJsonSchema2Pojo
    cp ./build/libs/bamboo-generator*-all.jar bamboo-generator.jar
    java -jar bamboo-generator.jar

You can of course also use the IDE of your choice to run, develop, and debug the different components, the above commands are just examples.

+++++++++++++
Other Systems
+++++++++++++

Seeing as Aeolus is meant to be a complementary tool to `Artemis <https://github.com/ls1intum/Artemis>`_, please refer to the Artemis documentation for more
information on how to set up a local development environment for Artemis, including the documentation on how to set up
`Jenkins <https://docs.artemis.cit.tum.de/dev/setup/jenkins-gitlab.html>`_ and `Bamboo <https://docs.artemis.cit.tum.de/dev/setup/bamboo-bitbucket-jira.html>`_ for local development.