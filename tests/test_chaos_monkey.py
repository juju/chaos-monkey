from unittest import TestCase

from mock import patch, call

from chaos_monkey import (
    ChaosMonkey,
    NotFound
)
from chaos_monkey_base import Chaos
from chaos.net import Net

__metaclass__ = type


class CommonTestBase(TestCase):

    def verify_equals_to_all_chaos(self, chaos):
        all_chaos, _ = ChaosMonkey.get_all_chaos()
        self.assertEqual(
            sorted(all_chaos, key=lambda k: k.command_str),
            sorted(chaos, key=lambda k: k.command_str))


class TestChaosMonkey(CommonTestBase):

    def test_factory(self):
        cm = ChaosMonkey.factory()
        self.assertIs(type(cm), ChaosMonkey)

    def test_get_all_chaos(self):
        cm = ChaosMonkey.factory()
        all_chaos, all_factory_obj = cm.get_all_chaos()
        self.assertItemsEqual(
            self._get_all_command_str(all_chaos),  self._command_strings())

    def test_run_random_chaos(self):
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        with patch('utility.check_output', autospec=True) as mock:
            cm.run_random_chaos(timeout=0)
        self.assertEqual(mock.called, True)

    def test_run_random_chaos_passes_timeout(self):
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        with patch('chaos_monkey.ChaosMonkey._run_command',
                   autospec=True) as mock:
            cm.run_random_chaos(timeout=1)
        self.assertEqual(1, mock.call_args_list[0][1]['timeout'])

    def test_run_chaos(self):
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        with patch('utility.check_output', autospec=True) as mock:
            cm.run_chaos('net', 'allow-ssh', timeout=0)
        mock.assert_called_once_with(['ufw', 'allow', 'ssh'])

    def test_run_chaos_passes_timeout(self):
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        with patch('chaos_monkey.ChaosMonkey._run_command',
                   autospec=True) as mock:
            cm.run_chaos('net', 'allow-ssh', timeout=0)
        self.assertEqual(0, mock.call_args_list[0][1]['timeout'])

    def test_run_chaos_raises_for_command_str(self):
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    NotFound,
                    "Command not found: group: net command_str:foo"):
                cm.run_chaos('net', 'foo', timeout=0)

    def test_run_chaos_raises_for_group(self):
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    NotFound,
                    "Command not found: group: bar command_str:allow-ssh"):
                cm.run_chaos('bar', 'allow-ssh', timeout=0)

    def test_run_command(self):
        cm = ChaosMonkey.factory()
        net = Net()
        chaos = Chaos(enable=net.deny_ssh, disable=net.allow_ssh,
                      group='net', command_str='deny-ssh')
        with patch('utility.check_output', autospec=True) as mock:
            cm._run_command(chaos, timeout=0)
        self.assertEqual(mock.mock_calls, [
            call(['ufw', 'deny', 'ssh']), call(['ufw', 'allow', 'ssh'])])

    def test_shutdown(self):
        cm = ChaosMonkey.factory()
        with patch('utility.check_output', autospec=True) as mock:
            cm.shutdown()
        mock.assert_any_call(['ufw', 'reset'])

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
        commands = ['deny-incoming', 'allow-ssh']
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
        commands = ['allow-ssh']
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.command_str != 'allow-ssh' for c in cm.chaos))

    def test_exclude_commands(self):
        commands = ['allow-ssh', 'jujud']
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.command_str not in commands for c in cm.chaos))

    def test_include_and_exclude_commands(self):
        commands = ['allow-ssh', 'jujud']
        cm = ChaosMonkey.factory()
        cm.include_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.command_str in commands for c in cm.chaos))
        cm.exclude_command(['jujud'])
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.command_str != 'jujud' for c in cm.chaos))

    def test_include_group_and_include_command(self):
        groups = ['net']
        commands = ['jujud']
        cm = ChaosMonkey.factory()
        cm.include_group(groups)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))
        cm.include_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(any(c.command_str == 'jujud' for c in cm.chaos))
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
        commands = ['deny-all', 'deny-ssh']
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
        commands = ['allow-ssh']
        cm = ChaosMonkey.factory()
        cm.include_group('all')
        cm.exclude_group(groups)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group != 'net' for c in cm.chaos))
        cm.include_command(commands)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(any(c.command_str == 'allow-ssh' for c in cm.chaos))
        self.assertTrue(any(c.group == 'net' for c in cm.chaos))

    def test_find_command(self):
        all_chaos, _ = ChaosMonkey.get_all_chaos()
        command = ChaosMonkey._find_command(all_chaos, 'deny-all')
        self.assertEqual(command.command_str, 'deny-all')

    def test_find_command_wrong_command(self):
        all_chaos, _ = ChaosMonkey.get_all_chaos()
        command = ChaosMonkey._find_command(all_chaos, 'foo')
        self.assertEqual(command, None)

    def _get_all_command_str(self, chaos):
        return [c.command_str for c in chaos]

    def _command_strings(self):
        return ['deny-all', 'deny-incoming', 'deny-outgoing', 'allow-ssh',
                'deny-ssh', 'jujud', 'mongod']
