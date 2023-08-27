import typing

from utils import logger


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
        actions: dict[str, typing.Any] = self.metadata.get("actions", {})
        for action in actions:
            if action == new_name:
                return actions[action].get("original_name", None)
        return None

    def get_meta_for_action(self, action: str) -> dict[str, typing.Any]:
        return self.metadata.get("actions", {}).get(action, {})

    def get(self, key: str) -> dict[str, typing.Any]:
        if key not in self.metadata:
            self.metadata[key] = {}
        return self.metadata.get(key, None)

    def set(self, key: str, value: typing.Any) -> None:
        self.metadata[key] = value

    def append(
        self, scope: str, key: str, subkey: str, value: typing.Any
    ) -> None:
        logger.debug("🧐", f"setting metadata: before -> {self.metadata}", True)
        if not self.has(scope=scope, key=key, subkey=None):
            if scope not in self.metadata:
                self.metadata[scope] = {}
            self.metadata[scope][key] = {subkey: value}

        self.metadata[scope][key][subkey] = value

        logger.debug("🧐", f"setting metadata: after -> {self.metadata}", True)

    def has(self, scope: str, key: str, subkey: typing.Optional[str]) -> bool:
        if scope not in self.metadata:
            return False
        if key not in self.metadata[scope]:
            return False
        if not subkey:
            return True
        return subkey in self.metadata[scope][key]
