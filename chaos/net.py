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
        self._actions.append(FirewallAction.enable())

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
        return [
            FirewallChaos(
                'deny-all',
                'Deny all incoming and outgoing network traffic except ssh.',
                allow_ssh,
                deny_in_to_any,
                deny_out_to_any,
                ),
            FirewallChaos(
                'deny-incoming',
                'Deny all incoming network traffic except ssh.',
                allow_ssh,
                deny_in_to_any,
                ),
            FirewallChaos(
                'deny-outgoing',
                'Deny all outgoing network traffic except ssh.',
                allow_ssh,
                deny_out_to_any,
                allow_in_to_any,
                ),
            FirewallChaos(
                'deny-state-server',
                'Deny network traffic to the Juju State-Server',
                FirewallAction.deny_port_rule(37017),
                allow_in_to_any,
                ),
            FirewallChaos(
                'deny-api-server',
                'Deny network traffic to the Juju API Server.',
                FirewallAction.deny_port_rule(17017),
                allow_in_to_any,
                ),
            FirewallChaos(
                'deny-sys-log',
                'Deny network traffic to the Juju SysLog.',
                FirewallAction.deny_port_rule(6514),
                allow_in_to_any,
                ),
        ]
