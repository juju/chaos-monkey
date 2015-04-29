from chaos_monkey_base import (
    Chaos,
    ChaosMonkeyBase,
)
from utility import (
    log,
    run_shell_command,
)

__metaclass__ = type


class Net(ChaosMonkeyBase):
    """Creates networking chaos."""

    def __init__(self):
        self.group = 'net'
        super(Net, self).__init__()

    @classmethod
    def factory(cls):
        return cls()

    def reset(self):
        log("Net.reset ")
        cmd = 'ufw reset'
        run_shell_command(cmd)

    def default_deny(self):
        log("Net.default_deny")
        cmd = "ufw default deny"
        run_shell_command(cmd)

    def default_allow(self):
        log("Net.default_allow")
        cmd = "ufw default allow"
        run_shell_command(cmd)

    def allow_ssh(self):
        log("Net.allow_ssh")
        cmd = 'ufw allow ssh'
        run_shell_command(cmd)

    def deny_ssh(self):
        log("Net.deny_ssh")
        cmd = 'ufw deny ssh'
        run_shell_command(cmd)

    def deny_all_incoming_and_outgoing_except_ssh(self):
        log("Net.deny_all_incoming_and_outgoing_except_ssh")
        self.deny_all_incoming_except_ssh()
        self.deny_all_outgoing_except_ssh()

    def allow_all_incoming_and_outgoing(self):
        log("Net.allow_all_incoming_and_outgoing")
        self.allow_all_incoming()
        self.allow_all_outgoing()

    def deny_all_incoming_except_ssh(self):
        log("Net.deny_all_incoming_except_ssh")
        self.allow_ssh()
        self.default_deny()

    def allow_all_incoming(self):
        log("Net.allow_all_incoming")
        self.default_allow()

    def deny_all_outgoing_except_ssh(self):
        log("Net.deny_all_outgoing_except_ssh")
        self.allow_ssh()
        cmd = 'ufw deny out to any'
        run_shell_command(cmd)

    def allow_all_outgoing(self):
        log("Net.allow_all_outgoing")
        cmd = 'ufw delete deny out to any'
        run_shell_command(cmd)

    def deny_port(self, port=8080):
        log("Net.deny_port port=%s" % port)
        cmd = 'ufw deny ' + str(port)
        run_shell_command(cmd)

    def get_chaos(self):
        chaos = list()
        chaos.append(
            Chaos(
                enable=self.deny_all_incoming_and_outgoing_except_ssh,
                disable=self.allow_all_incoming_and_outgoing,
                group=self.group,
                command_str='deny-all'))
        chaos.append(
            Chaos(
                enable=self.deny_all_incoming_except_ssh,
                disable=self.allow_all_incoming,
                group=self.group,
                command_str='deny-incoming'))
        chaos.append(
            Chaos(
                enable=self.deny_all_outgoing_except_ssh,
                disable=self.allow_all_outgoing,
                group=self.group,
                command_str='deny-outgoing'))
        chaos.append(
            Chaos(
                enable=self.allow_ssh,
                disable=None,
                group=self.group,
                command_str='allow-ssh'))
        chaos.append(
            Chaos(
                enable=self.deny_ssh,
                disable=self.allow_ssh,
                group=self.group,
                command_str='deny-ssh'))
        return chaos

    def shutdown(self):
        self.reset()
