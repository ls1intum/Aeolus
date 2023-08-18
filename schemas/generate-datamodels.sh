#!/usr/bin/env bash

source ./cli/venv/bin/activate
_pwd=$(pwd)
directory="schemas"
codegen_params="--target-python-version 3.11 --reuse-model --use-schema-description --input-file-type jsonschema --output-model-type pydantic_v2.BaseModel"
latest_schema_version=$(ls -1v "${_pwd}/${directory}" | tail -n 1)

cd ${_pwd}/${directory} || exit

echo "Generating datamodels for schema version ${latest_schema_version}"
cd "${_pwd}/${directory}/${latest_schema_version}" || exit

for schema in *.schema.json
do
  [[ -e "$schema" ]] || break
  filename=${schema/.schema.json/}
  echo "Generating $filename.py from $schema"
  datamodel-codegen ${codegen_params} --input "${schema}" --output "${_pwd}/cli/classes/generated/${filename}.py"
done
pwd
cd "${_pwd}/${directory}/${latest_schema_version}/environment" || exit
for schema in *.schema.json
do
  [[ -e "$schema" ]] || break
  filename=${schema/.schema.json/}
  echo "Generating $filename.py from $schema"
  datamodel-codegen ${codegen_params} --input ${schema} --output ${_pwd}/cli/classes/generated/${filename}.py
done
