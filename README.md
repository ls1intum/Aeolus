# Aeolus: A Domain-Specific Language for Streamlining CI Job Configuration for Programming Exercises

This repository will contain the work of [my](https://github.com/reschandreas) master's thesis. The goal of this thesis is to create a domain-specific language (DSL) for streamlining CI job configuration for programming exercises.

## Why?
Currently, in Artemis, it is tiresome to configure CI jobs that deviate from the standard templates.
Aeolus should help to make the configuration easier, more readable and most importantly more platform-independent.

## How?
The idea is to define an input grammar, parse and validate it and generate the CI configuration 
for multiple platforms (e.g. CLI, Bamboo, Jenkins, ...). And therefore be able to 
switch the CI platform without having to rewrite the configuration.