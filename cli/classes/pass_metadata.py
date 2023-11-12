"""
PassMetadata class.
"""
import typing

from cli_utils import logger


class PassMetadata:
    """
    Metadata class. Stores metadata to be used in passes.
    """

    metadata: dict[str, typing.Any] = {}

    def __init__(self, metadata: typing.Optional[dict[str, typing.Any]] = None) -> None:
        if not metadata:
            metadata = {}
        self.metadata = metadata

    def get_original_name_of(self, new_name: str) -> typing.Optional[str]:
        """
        Get the original name of an action.
        :param new_name:
        :return:
        """
        actions: dict[str, typing.Any] = self.metadata.get("actions", {})
        for action in actions:
            if action == new_name:
                return actions[action].get("original_name", None)
        return None

    def get_meta_for_action(self, action: str) -> dict[str, typing.Any]:
        """
        Get the metadata for an action.
        :param action:
        :return:
        """
        return self.metadata.get("actions", {}).get(action, {})

    def get(self, key: str) -> dict[str, typing.Any]:
        """
        Get the metadata for a key.
        :param key:
        :return:
        """
        if key not in self.metadata:
            self.metadata[key] = {}
        return self.metadata.get(key, None)

    def set(self, scope: str, value: typing.Any) -> None:
        """
        Set a metadata key.
        :param scope: metadata scope
        :param value: value to set
        """
        self.metadata[scope] = value

    def append(self, scope: str, key: str, subkey: str, value: typing.Any) -> None:
        """
        Append a value to a metadata key.
        :param scope: metadata scope
        :param key: metadata key
        :param subkey: metadata subkey
        :param value: value to append
        """
        logger.debug("🧐", f"setting metadata: before -> {self.metadata}", True)
        if not self.has(scope=scope, key=key, subkey=None):
            if scope not in self.metadata:
                self.metadata[scope] = {}
            self.metadata[scope][key] = {subkey: value}

        self.metadata[scope][key][subkey] = value

        logger.debug("🧐", f"setting metadata: after -> {self.metadata}", True)

    def has(self, scope: str, key: str, subkey: typing.Optional[str]) -> bool:
        """
        Check if a metadata key exists.
        :param scope: scope to check
        :param key: key to find
        :param subkey: subkey to find
        :return: True if the key exists, False otherwise
        """
        if scope not in self.metadata:
            return False
        if key not in self.metadata[scope]:
            return False
        if not subkey:
            return True
        return subkey in self.metadata[scope][key]
