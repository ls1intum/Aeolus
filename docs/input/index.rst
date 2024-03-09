Input Structure Overview
========================

Our input structure, as depicted below, is encapsulated within either a Windfile (highlighted in blue) or an Actionfile (highlighted in green). Designed for extensibility (NFR7), the structure comprises various components explained in the following sections.

.. figure:: ../figures/windfile_structure.pdf
   :width: 100%
   :alt: The structure of the input expected by Aeolus.

Windfiles
---------

Windfiles serve as the outermost layer, describing a CI job. They encompass essential information such as job actions, required repositories, and metadata like optional container images, callback URLs, or repository checkout credentials.

Actionfiles
------------

While Windfiles provide a complete configuration for multiple targets, Actionfiles partially define a job. They facilitate code reuse by importing externally implemented and open-source actions, akin to GitHub Actions' concept (`GitHub Actions <https://docs.github.com/en/actions/creating-actions/publishing-actions-in-github-marketplace>`_).

Action and Step
---------------

The smallest but crucial part of our input is the step or action. Actions, further specialized into steps, define the script executed in the target system. Two key terms distinguish Windfiles and Actionfiles: Steps are specialized actions not directly part of a Windfile, imported and converted into actions during code generation.

Script Action
^^^^^^^^^^^^^

The simplest action, a *Script Action*, is directly defined in a Windfile or Actionfile. It contains a shell script for execution in the target system.

.. code-block:: yaml
   :caption: Example of a Script Action in Aeolus.
   :name: lst-script-action

   - name: echo-action
     script: |
       echo "I can be used to write inlined code."

File Action
^^^^^^^^^^^

A *File Action* defines a file containing shell code, suitable for longer, more complex scripts. The script content is integrated into the final result and converted to a Script Action.

.. code-block:: yaml
   :caption: Example of a File Action in Aeolus.
   :name: lst-file-action

   - name: complicated-action
     file: overly-long-action.sh

Platform Action
^^^^^^^^^^^^^^^

*Platform Actions* serve two purposes: preparing the target CI system for other actions and providing platform-specific actions for specific targets.

- The first type executes Python code to dynamically prepare the CI system, using the target's interfaces, like API calls.

.. code-block:: yaml
   :caption: Example of a Platform Action using a Python Script in Aeolus.
   :name: lst-platform-action-python

   - name: install plugin
     platform: bamboo
     code: install-plugin.py
     function: run

- The second type caters to target-specific actions. These actions are excluded for non-matching targets.

.. code-block:: yaml
   :caption: Example of a Platform Action in Aeolus.
   :name: lst-platform-action

   - name: junit parser
     parameters:
       test_results: "**/tests/test/*.xml"
     platform: bamboo
     kind: junit
     runAlways: true

Template Action
^^^^^^^^^^^^^^^

*Template Actions* utilize Actionfiles within Windfiles, facilitating code sharing and reuse.

.. code-block:: yaml
   :caption: Example of a Template Action in Aeolus.
   :name: lst-template-action

   - name: open source action
     use: https://github.com/reschandreas/example-action.git
     parameters:
       WHO_TO_GREET: "thesis readers."

Results
-------

In Aeolus, the term "results" replaces "artifacts." Results, essential for assessing submissions, represent files indicating submission quality and compliance with the problem statement.

.. code-block:: yaml
   :caption: Example of results specified for an action in Aeolus.
   :name: lst-results

   results:
     - name: junit_**/tests/test/*.xml
       path: "**/tests/test/*.xml"
       type: junit

Docker Configuration
--------------------

To support multiple operating systems and other environments, Aeolus relies on containers.
The Docker configuration, as shown in our input diagram and exemplified below, allows specifying image, tag, volumes, and parameters.

.. code-block:: yaml
   :caption: Example of a Docker configuration in a Windfile.
   :name: lst-docker-config

     docker:
       image: ls1tum/artemis-maven-template
       tag: java17-20
       parameters:
         - --cpus=2

Environment Variables
----------------------

All action types can accept environment variables as input and script generalization. Template actions benefit from defining a set of environment variables for user customization.

Parameters
----------

Differentiating between parameters and environment variables, parameters are handled differently across target systems. An example in :ref:`lst-template-action` demonstrates parameter usage, allowing external actions to define and override parameter values.

Repositories
------------

A CI job in Aeolus processes exercise submissions from multiple repositories. The input definition supports a list of repositories checked out during execution.

.. code-block:: yaml
   :caption: Example of a repository in a Windfile.
   :name: lst-repository

   repositories:
     aeolus:
       url: https://github.com/ls1intum/Aeolus.git
       branch: develop
       path: repository

Targets
-------

Actions can possess the property "targets," specifying platforms where defined actions are needed. This property helps execute scripts on certain platforms while excluding them from others.

Lifecycle
---------

Aeolus supports dynamic action skipping during different exercise stages. Five stages are identified, and an action can be skipped during specific stages or all stages.

- ``preparation``: Instructor prepares exercise.
- ``working_time``: Students actively work on the exercise.
- ``post_deadline``: Working time ends; no more submissions allowed.
- ``evaluation``: Instructor evaluates submissions.
- ``all``: Action is skipped in all exercise stages.

.. code-block:: yaml
   :caption: Example of a skipped action during exercise preparation.
   :name: lst-skipped-action

   - name: echo-action
     script: echo "I will be skipped during preparation."
     excludeDuring:
       - preparation
