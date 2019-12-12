from .dotdict import DotDict
import collections


class Config:

    def __init__(self, config_defaults, config_custom):
        self.config = self.merge(config_custom, config_defaults)

    def generate(self):
        return DotDict(self.config)

    def merge(self, source, destination):
        for key, value in source.items():
            if isinstance(value, collections.abc.Mapping):
                node = destination.setdefault(key, {})
                self.merge(value, node)
            else:
                destination[key] = value

        return destination
