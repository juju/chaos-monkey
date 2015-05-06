import logging

from chaos_monkey_base import (
    Chaos,
    ChaosMonkeyBase,
)
from utility import (
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
        logging.info("Net.reset ")
        cmd = 'ufw reset'
        run_shell_command(cmd)

    def default_deny(self):
        logging.info("Net.default_deny")
        cmd = "ufw default deny"
        run_shell_command(cmd)

    def default_allow(self):
        logging.info("Net.default_allow")
        cmd = "ufw default allow"
        run_shell_command(cmd)

    def allow_ssh(self):
        logging.info("Net.allow_ssh")
        cmd = 'ufw allow ssh'
        run_shell_command(cmd)

    def deny_ssh(self):
        logging.info("Net.deny_ssh")
        cmd = 'ufw deny ssh'
        run_shell_command(cmd)

    def deny_all_incoming_and_outgoing_except_ssh(self):
        logging.info("Net.deny_all_incoming_and_outgoing_except_ssh")
        self.deny_all_incoming_except_ssh()
        self.deny_all_outgoing_except_ssh()

    def allow_all_incoming_and_outgoing(self):
        logging.info("Net.allow_all_incoming_and_outgoing")
        self.allow_all_incoming()
        self.allow_all_outgoing()

    def deny_all_incoming_except_ssh(self):
        logging.info("Net.deny_all_incoming_except_ssh")
        self.allow_ssh()
        self.default_deny()

    def allow_all_incoming(self):
        logging.info("Net.allow_all_incoming")
        self.default_allow()

    def deny_all_outgoing_except_ssh(self):
        logging.info("Net.deny_all_outgoing_except_ssh")
        self.allow_ssh()
        cmd = 'ufw deny out to any'
        run_shell_command(cmd)

    def allow_all_outgoing(self):
        logging.info("Net.allow_all_outgoing")
        cmd = 'ufw delete deny out to any'
        run_shell_command(cmd)

    def deny_port(self, port):
        logging.info("Net.deny_port port=%s" % port)
        cmd = 'ufw deny %s' % port
        run_shell_command(cmd)

    def allow_port(self, port):
        logging.info("Net.allow_port port=%s" % port)
        cmd = 'ufw delete deny %s' % port
        run_shell_command(cmd)

    def deny_state_server(self):
        logging.info("Net.deny_state_server")
        self.deny_port(37017)

    def allow_state_server(self):
        logging.info("Net.allow_state_server")
        self.allow_port(37017)

    def deny_api_server(self):
        logging.info("Net.deny_api_server")
        self.deny_port(17070)

    def allow_api_server(self):
        logging.info("Net.allow_api_server")
        self.allow_port(17070)

    def deny_sys_log(self):
        logging.info("Net.deny_sys_log")
        self.deny_port(6514)

    def allow_sys_log(self):
        logging.info("Net.allow_sys_log")
        self.allow_port(6514)

    def get_chaos(self):
        chaos = list()
        chaos.append(
            self._add_chaos(
                self.deny_all_incoming_and_outgoing_except_ssh,
                self.allow_all_incoming_and_outgoing, 'deny-all'))
        chaos.append(
            self._add_chaos(
                self.deny_all_incoming_except_ssh, self.allow_all_incoming,
                'deny-incoming'))
        chaos.append(
            self._add_chaos(
                self.deny_all_outgoing_except_ssh, self.allow_all_outgoing,
                'deny-outgoing'))
        chaos.append(self._add_chaos(self.allow_ssh, None, 'allow-ssh'))
        chaos.append(
            self._add_chaos(
                self.deny_state_server, self.allow_state_server,
                'deny-state-server'))
        chaos.append(
            self._add_chaos(
                self.deny_api_server, self.allow_api_server,
                'deny-api-server'))
        chaos.append(
            self._add_chaos(
                self.deny_sys_log, self.allow_sys_log, 'deny-sys-log'))
        return chaos

    def _add_chaos(self, enable, disable, command_str):
        return Chaos(enable=enable, disable=disable, group=self.group,
                     command_str=command_str)

    def shutdown(self):
        self.reset()
