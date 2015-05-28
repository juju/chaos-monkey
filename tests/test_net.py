from mock import patch, call

from chaos.net import (
    FirewallAction,
    Net,
)
from tests.common_test_base import CommonTestBase

__metaclass__ = type


class TestFirewallAction(CommonTestBase):

    def test_firewall_action(self):
        action = FirewallAction("on", "off")
        self.assertEqual(action.do_command, "on")
        self.assertEqual(action.undo_command, "off")
        self.assertEqual(repr(action), "FirewallAction('on', 'off')")

    def test_enable(self):
        action = FirewallAction.enable()
        self.assertEqual(action.do_command, "ufw --force enable")
        self.assertEqual(action.undo_command, "ufw disable")

    def test_rule(self):
        action = FirewallAction.rule("allow from 192.168.1.0/24")
        self.assertEqual(action.do_command, "ufw allow from 192.168.1.0/24")
        self.assertEqual(
            action.undo_command,
            "ufw delete allow from 192.168.1.0/24")

    def test_deny_port_rule(self):
        action = FirewallAction.deny_port_rule(80)
        self.assertEqual(action.do_command, "ufw deny 80")
        self.assertEqual(action.undo_command, "ufw delete deny 80")

    def test_deny_port_rule_only_number(self):
        self.assertRaises(ValueError, FirewallAction.deny_port_rule, "10")

    def test_do(self):
        action = FirewallAction("on", "off")
        with patch('utility.check_output', autospec=True) as mock:
            action.do()
        mock.assert_called_once_with(["on"])

    def test_undo(self):
        action = FirewallAction("on", "off")
        with patch('utility.check_output', autospec=True) as mock:
            action.undo()
        mock.assert_called_once_with(["off"])


allow_in_call = call(['ufw', 'allow', 'in', 'to', 'any'])
deny_in_call = call(['ufw', 'deny', 'in', 'to', 'any'])
deny_out_call = call(['ufw', 'deny', 'out', 'to', 'any'])
allow_ssh_call = call(['ufw', 'allow', 'ssh'])
enable_call = call(['ufw', '--force', 'enable'])
disable_call = call(['ufw', 'disable'])
delete_ssh_call = call(['ufw', 'delete', 'allow', 'ssh'])
delete_deny_out_call = call(['ufw', 'delete', 'deny', 'out', 'to', 'any'])
delete_deny_in_call = call(['ufw', 'delete', 'deny', 'in', 'to', 'any'])
delete_allow_in_call = call(['ufw', 'delete', 'allow', 'in', 'to', 'any'])


class TestNet(CommonTestBase):

    def setUp(self):
        self.setup_test_logging()

    def test_get_chaos(self):
        net = Net()
        chaos = net.get_chaos()
        self.assertItemsEqual(
            self.get_command_str(chaos), get_all_net_commands())
        for c in chaos:
            self.assertEqual('net', c.group)

    def test_shutdown(self):
        net = Net()
        with patch('utility.check_output', autospec=True) as mock:
            net.shutdown()
        mock.assert_called_once_with(['ufw', '--force', 'reset'])

    def get_net_chaos(self, cmd):
        net = Net()
        for chaos in net.get_chaos():
            if chaos.command_str == cmd:
                return chaos
        self.fail("{!r} not given as possible chaos".format(cmd))

    def assert_calls(self, function, expected_calls):
        with patch('utility.check_output', autospec=True) as mock:
            function()
        self.assertEqual(mock.mock_calls, expected_calls)

    def test_deny_all(self):
        chaos = self.get_net_chaos("deny-all")
        self.assert_calls(
            chaos.enable,
            [allow_ssh_call, deny_in_call, deny_out_call, enable_call])
        self.assert_calls(
            chaos.disable,
            [disable_call, delete_deny_out_call, delete_deny_in_call,
             delete_ssh_call])

    def test_deny_incoming(self):
        chaos = self.get_net_chaos("deny-incoming")
        self.assert_calls(
            chaos.enable,
            [allow_ssh_call, deny_in_call, enable_call])
        self.assert_calls(
            chaos.disable,
            [disable_call, delete_deny_in_call, delete_ssh_call])

    def test_deny_outgoing(self):
        chaos = self.get_net_chaos("deny-outgoing")
        self.assert_calls(
            chaos.enable,
            [allow_ssh_call, deny_out_call, allow_in_call, enable_call])
        self.assert_calls(
            chaos.disable,
            [disable_call, delete_allow_in_call, delete_deny_out_call,
             delete_ssh_call])

    def test_deny_state_server(self):
        chaos = self.get_net_chaos("deny-state-server")
        self.assert_calls(
            chaos.enable,
            [call(['ufw', 'deny', '37017']), allow_in_call, enable_call])
        self.assert_calls(
            chaos.disable,
            [disable_call, delete_allow_in_call,
             call(['ufw', 'delete', 'deny', '37017'])])

    def test_deny_api_server(self):
        chaos = self.get_net_chaos("deny-api-server")
        self.assert_calls(
            chaos.enable,
            [call(['ufw', 'deny', '17017']), allow_in_call, enable_call])
        self.assert_calls(
            chaos.disable,
            [disable_call, delete_allow_in_call,
             call(['ufw', 'delete', 'deny', '17017'])])

    def test_deny_sys_log(self):
        chaos = self.get_net_chaos("deny-sys-log")
        self.assert_calls(
            chaos.enable,
            [call(['ufw', 'deny', '6514']), allow_in_call, enable_call])
        self.assert_calls(
            chaos.disable,
            [disable_call, delete_allow_in_call,
             call(['ufw', 'delete', 'deny', '6514'])])


def get_all_net_commands():
    return ['deny-all', 'deny-incoming', 'deny-outgoing',  'deny-state-server',
            'deny-api-server', 'deny-sys-log']
