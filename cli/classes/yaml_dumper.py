import typing

import yaml


# Using custom dumper for more control
# pylint: disable=too-many-ancestors
class YamlDumper(yaml.Dumper):
    def represent_scalar(self, tag: typing.Any, value: typing.Any, style: typing.Any = None) -> typing.Any:
        """
        Represents a scalar.
        :param tag:
        :param value:
        :param style:
        :return:
        """
        if isinstance(value, str) and "\n" in value:
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return super().represent_scalar(tag, value, style="|")
        return super().represent_scalar(tag, value, style)
