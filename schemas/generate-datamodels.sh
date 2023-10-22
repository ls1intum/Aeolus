#!/usr/bin/env bash

source ./cli/venv/bin/activate
_pwd=$(pwd)
directory="schemas"
codegen_params="--target-python-version 3.11 --reuse-model --use-schema-description --disable-timestamp --input-file-type jsonschema --output-model-type pydantic_v2.BaseModel --disable-warnings"
latest_schema_version=$(ls -1v "${_pwd}/${directory}" | tail -n 1)

cd ${_pwd}/${directory} || exit

echo "Generating datamodels for schema version ${latest_schema_version}"

datamodel-codegen ${codegen_params} --input "${_pwd}/${directory}/${latest_schema_version}/schemas" --output "${_pwd}/cli/classes/generated/"
if ! command -v json2ts &> /dev/null
then
    echo "We need to install json2ts, if you don't want that, abort now. Otherwise, we'll wait 10 seconds..."
    sleep 10
    npm install -g json-schema-to-typescript
fi
cd "${_pwd}/${directory}/${latest_schema_version}/schemas" || exit
json2ts -i "${_pwd}/${directory}/${latest_schema_version}/schemas" -o "${_pwd}/playground/src/routes/classes/generated"