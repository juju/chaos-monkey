from unittest import TestCase

from mock import patch, call

from chaos.net import Net


class TestNet(TestCase):

    def _run_test(self, method_call, assert_args):
        net = Net()
        with patch('utility.check_output', autospec=True) as mock:
            getattr(net, method_call)()
        mock.assert_called_once_with(assert_args)

    def _run_mock_calls(self, method_call, call_list):
        net = Net()
        with patch('utility.check_output', autospec=True) as mock:
            getattr(net, method_call)()
        self.assertEqual(mock.mock_calls, call_list)

    def test_reset(self):
        self._run_test('reset', ['ufw', 'reset'])

    def test_default_deny(self):
        self._run_test('default_deny', ['ufw', 'default', 'deny'])

    def test_default_allow(self):
        self._run_test('default_allow', ['ufw', 'default', 'allow'])

    def test_allow_ssh(self):
        self._run_test('allow_ssh', ['ufw', 'allow', 'ssh'])

    def test_deny_ssh(self):
        self._run_test('deny_ssh', ['ufw', 'deny', 'ssh'])

    def test_deny_all_incoming_and_outgoing_except_ssh(self):
        self._run_mock_calls(
            'deny_all_incoming_and_outgoing_except_ssh',
            [self._allow_ssh_call(), self._default_deny_call(),
             self._allow_ssh_call(),
             call(['ufw', 'deny', 'out', 'to', 'any'])])

    def test_allow_all_incoming_and_outgoing(self):
        self._run_mock_calls(
            'allow_all_incoming_and_outgoing',
            [self._default_allow_call(),
             call(['ufw', 'delete', 'deny', 'out', 'to', 'any'])])

    def test_deny_all_incoming_except_ssh(self):
        self._run_mock_calls(
            'deny_all_incoming_except_ssh',
            [self._allow_ssh_call(), self._default_deny_call()])

    def test_allow_all_incoming(self):
        self._run_test('allow_all_incoming', ['ufw', 'default', 'allow'])

    def test_deny_all_outgoing_except_ssh(self):
        self._run_mock_calls(
            'deny_all_outgoing_except_ssh',
            [self._allow_ssh_call(),
             call(['ufw', 'deny', 'out', 'to', 'any'])])

    def test_allow_all_outgoing(self):
        self._run_test(
            'allow_all_outgoing',
            ['ufw', 'delete', 'deny', 'out', 'to', 'any'])

    def test_deny_port(self):
        self._run_test(
            'deny_port', ['ufw', 'deny', '8080'])

    def test_get_chaos(self):
        net = Net()
        chaos = net.get_chaos()
        self.assertEqual(len(chaos),  5)
        self.assertItemsEqual(
            self._get_all_command_str(chaos), self._command_strings())
        for c in chaos:
            self.assertEqual('net', c.group)

    def _get_all_command_str(self, chaos):
        return [c.command_str for c in chaos]

    def _command_strings(self):
        return ['deny-all', 'deny-incoming', 'deny-outgoing', 'allow-ssh',
                'deny-ssh']

    def test_shutdown(self):
        self._run_test('reset', ['ufw', 'reset'])

    def _allow_ssh_call(self):
        return call(['ufw', 'allow', 'ssh'])

    def _default_deny_call(self):
        return call(['ufw', 'default', 'deny'])

    def _default_allow_call(self):
        return call(['ufw', 'default', 'allow'])
