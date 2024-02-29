*******
Jenkins
*******

Jenkins is a popular and powerful CI solution. With Jenkins, you can create pipelines using the DSL Groovy, which is
based on Java. Jenkins is a very flexible tool and can be used to create complex pipelines.

++++++++++++++++++++++++++
What does Aeolus generate?
++++++++++++++++++++++++++

Aeolus generates a simple Jenkinsfile, that is then used in a simple pipeline. Each action from the input file is
translated into a stage in the Jenkinsfile.