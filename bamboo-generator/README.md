## Aeolus Bamboo Generator

This small, but handy tool came into existence from the necessity to use the 
Bamboo YAML/Java specs to generate Bamboo build plans. There are no other ways
to reliably create Bamboo build plans, and the Bamboo REST API is not very
useful for this purpose.

# What?
This tool is essentially a wrapper around the maven plugin of bamboo-specs. It
allows you to generate Bamboo build plans from a YAML file. The YAML file is in the format
set by aeolus and in this Java application we convert it into the format that
bamboo-specs expects.

# How?
We read the YAML file and take the values we need to create working build plans containing custom 
stages und tasks. For this to work we have spezified the aeolus format to be vaguely enough to 
allow for as many different CI targets and still work with Bamboo.

# What is special about the Bamboo YAML format?
Well, it's the only format Bamboo understands, and it's not really readable or usable without the maven plugin. 
We only use the Bamboo YAML specs to talk to Bamboo.

# What was adapted in Aeolus to work with Bamboo?
We have added a new field to definition of a platform action in , called `kind`. This is used for the special 
use case of parsing the output of a build job so that Bamboo can interpret it correctly (i.e. it shows how many 
tests there are, how many passed etc.). This step does not make any sene in other CI targets, so we have added
this field to the aeolus format to support it. For now, the only acceptable value is `junit` and actions with that
value will be translated into a `TestParserTask` instead of the default `ScriptTask`.
