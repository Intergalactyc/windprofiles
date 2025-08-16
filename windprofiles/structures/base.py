from abc import ABC


class BaseData(ABC):
    # holds general metadata
    def __init__(self, metadata: dict):
        self._metadata = metadata

    def get_metadata(self, name=None):
        if not name:
            return self._metadata
        return self._metadata.get(name)

    def update_metadata(self, updater: dict):
        self._metadata.update(updater)
