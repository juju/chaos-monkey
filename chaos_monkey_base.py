import abc

__metaclass__ = type


class ChaosMonkeyBase:
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_chaos(self):
        raise NotImplemented

    @abc.abstractmethod
    def shutdown(self):
        raise NotImplemented


class Chaos:

    def __init__(self, enable, disable, group, command_str):
        self.enable = enable
        self.disable = disable
        self.group = group
        self.command_str = command_str
