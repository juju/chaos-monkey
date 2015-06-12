# Copyright 2015 Canonical Ltd.
# Licensed under the AGPLv3, see LICENCE file for details.
import abc

__metaclass__ = type


class ChaosMonkeyBase:
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_chaos(self):
        """Overridden by derived class and return Chaos objects.

        :return: List of Chaos.
        """
        raise NotImplemented


class Chaos:

    def __init__(self, enable, disable, group, command_str, description):
        self.enable = enable
        self.disable = disable
        self.group = group
        self.command_str = command_str
        self.description = description

    def __eq__(self, other):
        return self.command_str == other.command_str
