******
Bamboo
******

Bamboo is an Atlassian product for CI/CD.
Within Bamboo, you use so called Build Plans to define the steps that are executed to build and deploy your software.

Aeolus uses the Bamboo YAML Specs plugin to generate build plans from the input, as the plugin is only
usable with Java, the subsystem is implemented in said language and can be used as a standalone REST API or as a
container that is started if the target system is Bamboo.

+++++++++++++++++++
Bamboo Subcomponent
+++++++++++++++++++

The Bamboo subcomponent is a small Java Spring Boot application that generates the Bamboo build plan configuration for
Bamboo. It is a simple RESTful service that takes a JSON payload and returns the build plan in a JSON format or directly
generates the build plan in Bamboo.

## What does Aeolus generate?

Aeolus always tries to generate a simple and clean build plan, if the windfile contains a single docker configuration,
the generated build plan will be a single stage that uses the defined docker image and runs the defined commands inside it.
Whenever the windfile contains multiple docker configurations, Aeolus will generate a multi-stage build plan, where each
stage is a separate docker build and run step, the same applies if some actions need to be skipped or executed conditionally.
