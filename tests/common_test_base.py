from unittest import TestCase

from chaos_monkey import ChaosMonkey

__metaclass__ = type


class CommonTestBase(TestCase):

    def verify_equals_to_all_chaos(self, chaos):
        all_chaos, _ = ChaosMonkey.get_all_chaos()
        self.assertEqual(
            sorted(all_chaos, key=lambda k: k.command_str),
            sorted(chaos, key=lambda k: k.command_str))

    def get_command_str(self, chaos):
        return [c.command_str for c in chaos]
