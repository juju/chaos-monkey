# Copyright 2015 Canonical Ltd.
# Licensed under the AGPLv3, see LICENCE file for details.
from chaos_monkey_base import (
    Chaos,
    ChaosMonkeyBase,
)
from utility import (
    run_shell_command,
)

__metaclass__ = type


class FirewallAction:
    """FirewallAction encapsulates a ufw command and a means of undoing it."""

    def __init__(self, do_command, undo_command):
        self.do_command = do_command
        self.undo_command = undo_command

    def __repr__(self):
        return "{}({!r}, {!r})".format(
            self.__class__.__name__, self.do_command, self.undo_command)

    @classmethod
    def enable(cls):
        """Gives an action for enabling and disabling the firewalling."""
        return cls("ufw --force enable", "ufw disable")

    @classmethod
    def rule(cls, rule):
        """Gives an action for creating and deleting a given firewall rule."""
        if rule.startswith('netem'):
            return cls('tc qdisc add dev eth0 root {}'.format(rule),
                       'tc qdisc del dev eth0 root')
        return cls("ufw {}".format(rule), "ufw delete {}".format(rule))

    @classmethod
    def deny_port_rule(cls, port):
        """Gives an action for allowing and denying a particular port."""
        return cls.rule("deny {:d}".format(port))

    def do(self):
        """Runs command changing the firewall behaviour."""
        run_shell_command(self.do_command)

    def undo(self):
        """Runs command reverting the firewall behaviour that was changed."""
        run_shell_command(self.undo_command)


class FirewallChaos(Chaos):
    """FirewallChaos contains a particular firewall chaos operation to run."""

    group = "net"

    def __init__(self, name, description, *actions):
        self.command_str = name
        self.description = description
        self._actions = list(actions)

    def enable(self):
        for actions in self._actions:
            actions.do()

    def disable(self):
        for actions in reversed(self._actions):
            actions.undo()


class Net(ChaosMonkeyBase):
    """Net generates chaos actions that affect networking on a machine."""

    def __init__(self):
        super(Net, self).__init__()

    @classmethod
    def factory(cls):
        return cls()

    def get_chaos(self):
        allow_ssh = FirewallAction.rule("allow ssh")
        allow_in_to_any = FirewallAction.rule("allow in to any")
        deny_in_to_any = FirewallAction.rule("deny in to any")
        deny_out_to_any = FirewallAction.rule("deny out to any")
        delay = FirewallAction.rule(
            "netem delay 300ms 20ms distribution normal")
        delay_long = FirewallAction.rule(
            'netem delay 5s 1s distribution normal')
        drop = FirewallAction.rule('netem loss 50% 30%')
        corrupt = FirewallAction.rule('netem corrupt 50% 30%')
        duplicate = FirewallAction.rule('netem duplicate 50% 30%')
        return [
            FirewallChaos(
                'deny-all',
                'Deny all incoming and outgoing network traffic except ssh.',
                allow_ssh,
                deny_in_to_any,
                deny_out_to_any,
                FirewallAction.enable()
                ),
            FirewallChaos(
                'deny-incoming',
                'Deny all incoming network traffic except ssh.',
                allow_ssh,
                deny_in_to_any,
                FirewallAction.enable()
                ),
            FirewallChaos(
                'deny-outgoing',
                'Deny all outgoing network traffic except ssh.',
                allow_ssh,
                deny_out_to_any,
                allow_in_to_any,
                FirewallAction.enable()
                ),
            FirewallChaos(
                'deny-state-server',
                'Deny network traffic to the Juju State-Server',
                FirewallAction.deny_port_rule(37017),
                allow_in_to_any,
                FirewallAction.enable()
                ),
            FirewallChaos(
                'deny-api-server',
                'Deny network traffic to the Juju API Server.',
                FirewallAction.deny_port_rule(17017),
                allow_in_to_any,
                FirewallAction.enable()
                ),
            FirewallChaos(
                'deny-sys-log',
                'Deny network traffic to the Juju SysLog.',
                FirewallAction.deny_port_rule(6514),
                allow_in_to_any,
                FirewallAction.enable()
                ),
            FirewallChaos(
                'delay',
                'Delay network traffic.',
                delay,
                ),
            FirewallChaos(
                'delay-long',
                'Delay network traffic.',
                delay_long,
                ),
            FirewallChaos(
                'drop',
                'Drop network packets.',
                drop,
                ),
            FirewallChaos(
                'corrupt',
                'Corrupt network packets.',
                corrupt,
            ),
            FirewallChaos(
                'duplicate',
                'Duplicate network packets.',
                duplicate,
            ),


        ]
