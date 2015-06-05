from chaos_monkey import (
    ChaosMonkey,
)
from chaos.kill import Kill
from tests.common_test_base import CommonTestBase
from tests.test_kill import get_all_kill_commands
from tests.test_net import get_all_net_commands

__metaclass__ = type


class TestChaosMonkey(CommonTestBase):

    def setUp(self):
        self.setup_test_logging()

    def test_factory(self):
        cm = ChaosMonkey.factory()
        self.assertIs(type(cm), ChaosMonkey)

    def test_get_all_chaos(self):
        cm = ChaosMonkey.factory()
        all_chaos, all_factory_obj = cm.get_all_chaos()
        self.assertItemsEqual(
            self._get_command_str(all_chaos),  self._get_all_command_strings())

    def test_include_group(self):
        group = ['net']
        cm = ChaosMonkey.factory()
        cm.include_group(group)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))

    def test_include_group_empty(self):
        group = []
        cm = ChaosMonkey.factory()
        cm.include_group(group)
        self.assertEqual(cm.chaos, [])

    def test_include_group_multiple_groups(self):
        group = ['net', 'kill']
        cm = ChaosMonkey.factory()
        cm.include_group(group)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group in group for c in cm.chaos))

    def test_include_group_wrong_group_name(self):
        group = ['net', 'kill', 'foo']
        cm = ChaosMonkey.factory()
        cm.include_group(group)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group != 'foo' for c in cm.chaos))

    def test_exclude_group(self):
        group = ['net']
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_group(group)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group != 'net' for c in cm.chaos))

    def test_exclude_group_multiple_groups(self):
        group = ['net', 'kill']
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_group(group)
        self.assertTrue(all(c.group != 'net' for c in cm.chaos))
        self.assertTrue(all(c.group != 'kill' for c in cm.chaos))

    def test_exclude_group_empty(self):
        group = []
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_group(group)
        self.verify_equals_to_all_chaos(cm.chaos)

    def test_exclude_group_wrong_group_name(self):
        group = ['foo']
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_group(group)
        self.verify_equals_to_all_chaos(cm.chaos)

    def test_include_and_exclude_group(self):
        group = ['net', 'kill']
        cm = ChaosMonkey.factory()
        cm.include_group(group)
        self.assertTrue(any(c.group == 'net' for c in cm.chaos))
        self.assertTrue(any(c.group == 'kill' for c in cm.chaos))
        cm.exclude_group(['kill'])
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))

    def test_exclude_and_include_group(self):
        group = ['kill']
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_group(group)
        self.assertTrue(all(c.group != 'kill' for c in cm.chaos))
        cm.include_group(['kill'])
        self.assertTrue(all(c.group == 'kill' for c in cm.chaos))

    def test_include_command(self):
        command = ['deny-incoming']
        cm = ChaosMonkey.factory()
        cm.include_command(command)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(
            all(c.command_str == 'deny-incoming' for c in cm.chaos))

    def test_include_command_multiple_commands(self):
        commands = ['deny-incoming', 'deny-all']
        cm = ChaosMonkey.factory()
        cm.include_command(commands)
        self.assertEqual(len(cm.chaos), 2)
        self.assertTrue(all(c.command_str in commands for c in cm.chaos))

    def test_include_command_wrong_command(self):
        commands = ['foo']
        cm = ChaosMonkey.factory()
        cm.include_command(commands)
        self.assertEqual(cm.chaos, [])

    def test_exclude_command(self):
        commands = ['deny-all']
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.command_str != 'deny-all' for c in cm.chaos))

    def test_exclude_commands(self):
        commands = ['deny-all', Kill.jujud_cmd]
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.command_str not in commands for c in cm.chaos))

    def test_include_and_exclude_commands(self):
        commands = ['deny-all', Kill.jujud_cmd]
        cm = ChaosMonkey.factory()
        cm.include_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.command_str in commands for c in cm.chaos))
        cm.exclude_command([Kill.jujud_cmd])
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.command_str != Kill.jujud_cmd for c in cm.chaos))

    def test_include_group_and_include_command(self):
        groups = ['net']
        commands = [Kill.jujud_cmd]
        cm = ChaosMonkey.factory()
        cm.include_group(groups)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))
        cm.include_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(any(c.command_str == Kill.jujud_cmd for c in cm.chaos))
        self.assertTrue(any(c.group == 'net' for c in cm.chaos))
        self.assertTrue(any(c.group == 'kill' for c in cm.chaos))

    def test_include_group_and_exclude_command(self):
        groups = ['net']
        commands = ['deny-all']
        cm = ChaosMonkey.factory()
        cm.include_group(groups)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))
        cm.exclude_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))
        self.assertTrue(all(c.command_str != 'deny-all' for c in cm.chaos))

    def test_include_group_and_exclude_commands(self):
        groups = ['net']
        commands = ['deny-all', 'deny-incoming']
        cm = ChaosMonkey.factory()
        cm.include_group(groups)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))
        cm.exclude_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))
        self.assertTrue(all(c.command_str not in commands for c in cm.chaos))

    def test_exclude_group_and_include_command(self):
        groups = ['net']
        commands = ['deny-all']
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_group(groups)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group != 'net' for c in cm.chaos))
        cm.include_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(any(c.command_str == 'deny-all' for c in cm.chaos))
        self.assertTrue(any(c.group == 'net' for c in cm.chaos))

    def test_find_command(self):
        all_chaos, _ = ChaosMonkey.get_all_chaos()
        command = ChaosMonkey._find_command(all_chaos, 'deny-all')
        self.assertEqual(command.command_str, 'deny-all')

    def test_find_command_wrong_command(self):
        all_chaos, _ = ChaosMonkey.get_all_chaos()
        command = ChaosMonkey._find_command(all_chaos, 'foo')
        self.assertEqual(command, None)

    def test_get_groups(self):
        cm = ChaosMonkey.factory()
        all_chaos, _ = cm.get_all_chaos()
        group = cm.get_groups(['net'], all_chaos)
        self.assertGreaterEqual(len(group), 1)
        self.assertTrue(all(c.group == 'net' for c in group))

    def test_get_groups_multiple_groups(self):
        cm = ChaosMonkey.factory()
        all_chaos, _ = cm.get_all_chaos()
        group = cm.get_groups(['net', 'kill'], all_chaos)
        self.assertGreaterEqual(len(group), 1)
        self.assertTrue(
            all(c.group == 'net' or c.group == 'kill' for c in group))
        self.assertTrue(any(c.group == 'net' for c in group))
        self.assertTrue(any(c.group == 'kill' for c in group))

    def test_get_all_commands(self):
        all_commands = ChaosMonkey.get_all_commands()
        self.assertItemsEqual(all_commands, self._get_all_command_strings())

    def test_get_all_groups(self):
        all_groups = ChaosMonkey.get_all_groups()
        self.assertItemsEqual(all_groups, self._get_all_groups())

    def _get_command_str(self, chaos):
        return [c.command_str for c in chaos]

    def _get_all_command_strings(self):
        return get_all_net_commands() + get_all_kill_commands()

    def _get_all_groups(self):
        return ['net', Kill.group]
