from unittest import TestCase

from mock import patch, call

from chaos_monkey import ChaosMonkey, NotFound
from chaos_monkey_base import Chaos
from chaos.net import Net


class TestChaosMonkey(TestCase):

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
        with patch('utility.check_output', autospec=True) as mock:
            cm.run_random_chaos(timeout=0)
        self.assertEqual(mock.called, True)

    def test_run_random_chaos_passes_timeout(self):
        cm = ChaosMonkey.factory()
        with patch('chaos_monkey.ChaosMonkey._run_command',
                   autospec=True) as mock:
            cm.run_random_chaos(timeout=1)
        self.assertEqual(1, mock.call_args_list[0][1]['timeout'])

    def test_run_chaos(self):
        cm = ChaosMonkey.factory()
        with patch('utility.check_output', autospec=True) as mock:
            cm.run_chaos('net', 'allow-ssh', timeout=0)
        mock.assert_called_once_with(['ufw', 'allow', 'ssh'])

    def test_run_chaos_passes_timeout(self):
        cm = ChaosMonkey.factory()
        with patch('chaos_monkey.ChaosMonkey._run_command',
                   autospec=True) as mock:
            cm.run_chaos('net', 'allow-ssh', timeout=0)
        self.assertEqual(0, mock.call_args_list[0][1]['timeout'])

    def test_run_chaos_raises_for_command_str(self):
        cm = ChaosMonkey.factory()
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    NotFound,
                    "Command not found: group: net command_str:foo"):
                cm.run_chaos('net', 'foo', timeout=0)

    def test_run_chaos_raises_for_group(self):
        cm = ChaosMonkey.factory()
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

    def _get_all_command_str(self, chaos):
        return [c.command_str for c in chaos]

    def _command_strings(self):
        return ['deny-all', 'deny-incoming', 'deny-outgoing', 'allow-ssh',
                'deny-ssh', 'jujud', 'mongod']
