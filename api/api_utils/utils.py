from typing import Any

import yaml


def dump_yaml(content: Any) -> str:
    """
    Dump the given json to yaml.
    :param content: content to dump
    :return: yaml in string format
    """
    return yaml.dump(yaml.safe_load(content.model_dump_json(exclude_none=True)), sort_keys=False)


def remove_none_values(content: Any) -> Any:
    """
    Remove None values from the given object.
    :param content: content to remove None values from
    :return: objecy without None values
    """
    for key, value in list(content.dict().items()):
        if value is None:
            delattr(content, key)