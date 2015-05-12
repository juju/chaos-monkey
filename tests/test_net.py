from mock import patch, call

from chaos_monkey_base import Chaos
from chaos.net import Net
from tests.common_test_base import CommonTestBase

__metaclass__ = type


class TestNet(CommonTestBase):

    def _run_test(self, method_call, assert_args, **kwargs):
        net = Net()
        with patch('utility.check_output', autospec=True) as mock:
            getattr(net, method_call)(**kwargs)
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
            'deny_port', ['ufw', 'deny', '8080'], port=8080)

    def test_allow_port(self):
        self._run_test(
            'allow_port', ['ufw', 'delete', 'deny', '8080'], port=8080)

    def test_deny_state_server(self):
        self._run_test('deny_state_server', ['ufw', 'deny', '37017'])

    def test_allow_state_server(self):
        self._run_test(
            'allow_state_server', ['ufw', 'delete', 'deny', '37017'])

    def test_deny_api_server(self):
        self._run_test('deny_api_server', ['ufw', 'deny', '17070'])

    def test_allow_api_server(self):
        self._run_test('allow_api_server', ['ufw', 'delete', 'deny', '17070'])

    def test_deny_sys_log(self):
        self._run_test('deny_sys_log', ['ufw', 'deny', '6514'])

    def test_allow_sys_log(self):
        self._run_test('allow_sys_log', ['ufw', 'delete', 'deny', '6514'])

    def test_get_chaos(self):
        net = Net()
        chaos = net.get_chaos()
        self.assertItemsEqual(
            self.get_command_str(chaos), get_all_net_commands())
        for c in chaos:
            self.assertEqual('net', c.group)

    def test_create_chaos(self):
        net = Net()
        chaos = net.create_chaos('enable', 'disable', 'command', 'description')
        self.assertIs(type(chaos), Chaos)
        self.assertEqual(chaos.enable, 'enable')
        self.assertEqual(chaos.disable, 'disable')
        self.assertEqual(chaos.group, 'net')
        self.assertEqual(chaos.command_str, 'command')
        self.assertEqual(chaos.description, 'description')

    def test_shutdown(self):
        self._run_test('reset', ['ufw', 'reset'])

    def _allow_ssh_call(self):
        return call(['ufw', 'allow', 'ssh'])

    def _default_deny_call(self):
        return call(['ufw', 'default', 'deny'])

    def _default_allow_call(self):
        return call(['ufw', 'default', 'allow'])


def get_all_net_commands():
    return ['deny-all', 'deny-incoming', 'deny-outgoing',  'deny-state-server',
            'deny-api-server', 'deny-sys-log']
