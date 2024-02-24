***********************
Bamboo Specs Generation
***********************

Bamboo is an Atlassian product for CI/CD.
Within Bamboo, you use so called Build Plans to define the steps that are executed to build and deploy your software.

Aeolus uses the Bamboo YAML Specs plugin to generate build plans from the input, as the plugin is only
usable with Java, the subsystem is implemented in said language and can be used as a standalone REST API or as a
container that is started if the target system is Bamboo.

**************************
What does Aeolus generate?
**************************

Aeolus generates