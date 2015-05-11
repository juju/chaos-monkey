import logging

from mock import patch, call

from chaos_monkey_base import Chaos
from chaos.net import Net
from tests.common_test_base import CommonTestBase

__metaclass__ = type


class TestNet(CommonTestBase):

    def setUp(self):
        self.logger = logging.getLogger()
        self.orig_handlers = self.logger.handlers
        self.logger.handlers = []
        self.orig_level = self.logger.level

    def tearDown(self):
        self.logger.handlers = self.orig_handlers
        self.logger.level = self.orig_level

    def test_reset(self):
        self._assert_mock_calls('shutdown', [call(['ufw', 'reset'])])

    def test_deny_all_incoming_and_outgoing_except_ssh(self):
        cmd = ['allow_ssh_str', 'default_deny_str', 'deny_out_to_any_str']
        self._assert_mock_calls('deny_all_incoming_and_outgoing_except_ssh',
                                self._get_attr_calls(cmd, enable=True))

    def test_allow_all_incoming_and_outgoing(self):
        cmd = ['delete_ssh_str', 'default_allow_str',
               'delete_deny_out_to_any_str']
        self._assert_mock_calls('allow_all_incoming_and_outgoing',
                                self._get_attr_calls(cmd, enable=False))

    def test_deny_all_incoming_except_ssh(self):
        cmd = ['allow_ssh_str', 'default_deny_str']
        self._assert_mock_calls('deny_all_incoming_except_ssh',
                                self._get_attr_calls(cmd, enable=True))

    def test_allow_all_incoming(self):
        cmd = ['delete_ssh_str', 'default_allow_str']
        self._assert_mock_calls('allow_all_incoming',
                                self._get_attr_calls(cmd, enable=False))

    def test_deny_all_outgoing_except_ssh(self):
        cmd = ['allow_ssh_str', 'deny_out_to_any_str']
        self._assert_mock_calls('deny_all_outgoing_except_ssh',
                                self._get_attr_calls(cmd, enable=True))

    def test_allow_all_outgoing(self):
        cmd = ['delete_ssh_str', 'delete_deny_out_to_any_str']
        self._assert_mock_calls('allow_all_outgoing',
                                self._get_attr_calls(cmd, enable=False))

    def test_deny_port(self):
        self._assert_mock_calls(
            'deny_port',  self._get_attr_calls('ufw deny 8080', enable=True),
            port=8080)

    def test_allow_port(self):
        self._assert_mock_calls(
            'allow_port',
            self._get_attr_calls('ufw delete deny 8080', enable=False),
            port=8080)

    def test_deny_state_server(self):
        self._assert_mock_calls(
            'deny_state_server',
            self._get_attr_calls('ufw deny 37017', enable=True))

    def test_allow_state_server(self):
        self._assert_mock_calls(
            'allow_state_server',
            self._get_attr_calls('ufw delete deny 37017', enable=False))

    def test_deny_api_server(self):
        self._assert_mock_calls(
            'deny_api_server',
            self._get_attr_calls('ufw deny 17070', enable=True))

    def test_allow_api_server(self):
        self._assert_mock_calls(
            'allow_api_server',
            self._get_attr_calls('ufw delete deny 17070', enable=False))

    def test_deny_sys_log(self):
        self._assert_mock_calls(
            'deny_sys_log', self._get_attr_calls('ufw deny 6514', enable=True))

    def test_allow_sys_log(self):
        self._assert_mock_calls(
            'allow_sys_log',
            self._get_attr_calls('ufw delete deny 6514', enable=False))

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
        self._assert_mock_calls('shutdown', [call(['ufw', 'reset'])])

    def _assert_mock_calls(self, method_call, call_list, **kwargs):
        net = Net()
        with patch('utility.check_output', autospec=True) as mock:
            getattr(net, method_call)(**kwargs)
        self.assertEqual(mock.mock_calls, call_list)

    def _get_attr_calls(self, attrs, enable):
        net = Net()
        default_allow_call = ([call(net.default_allow_str.split(' '))]
                              if enable else [])
        if type(attrs) is list:
            cmd_calls = [call(getattr(net, attr).split(' ')) for attr in attrs]
        else:
            cmd_calls = [call(attrs.split(' '))]
        enable_call = ([call(['ufw', 'enable'])]
                       if enable else [call(['ufw', 'disable'])])
        return default_allow_call + cmd_calls + enable_call


def get_all_net_commands():
    return ['deny-all', 'deny-incoming', 'deny-outgoing',  'deny-state-server',
            'deny-api-server', 'deny-sys-log']
