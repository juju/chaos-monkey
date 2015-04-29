import random
from time import sleep

from chaos import (
    kill,
    net
)
from utility import NotFound

__metaclass__ = type


class ChaosMonkey:
    """Runs chaos monkey commands."""

    def __init__(self, chaos, factory_obj):
        self.chaos = chaos
        self.factory_obj = factory_obj

    @classmethod
    def factory(cls):
        all_chaos, factory_obj = ChaosMonkey.get_all_chaos()
        return cls(all_chaos, factory_obj)

    @staticmethod
    def get_all_chaos():
        all_chaos = []
        all_factory_obj = []
        factories = [net.Net.factory, kill.Kill.factory]
        for factory in factories:
            factory_obj = factory()
            all_factory_obj.append(factory_obj)
            all_chaos.extend(factory_obj.get_chaos())
        return all_chaos, all_factory_obj

    def run_random_chaos(self, timeout=2):
        random_chaos = random.choice(self.chaos)
        self._run_command(random_chaos, timeout=timeout)

    def run_chaos(self, group, command_str, timeout=2):
        command_found = False
        for chaos in self.chaos:
            if chaos.group == group and chaos.command_str == command_str:
                command_found = True
                self._run_command(chaos, timeout=timeout)
        if not command_found:
            raise NotFound("Command not found: group: %s command_str:%s" % (
                group, command_str))

    def _run_command(self, chaos, timeout=2):
        chaos.enable()
        sleep(timeout)
        if chaos.disable:
            chaos.disable()

    def shutdown(self):
        for obj in self.factory_obj:
            obj.shutdown()
