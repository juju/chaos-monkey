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

    @property
    def default_deny_str(self):
        return "ufw default deny"

    @property
    def default_allow_str(self):
        return "ufw default allow"

    @property
    def allow_ssh_str(self):
        return 'ufw allow ssh'

    @property
    def delete_ssh_str(self):
        return 'ufw delete allow ssh'

    @property
    def deny_out_to_any_str(self):
        return 'ufw deny out to any'

    @property
    def delete_deny_out_to_any_str(self):
        return 'ufw delete deny out to any'

    def reset(self):
        cmd = 'ufw --force reset'
        self.run_command(cmd)

    def deny_all_incoming_and_outgoing_except_ssh(self):
        cmd = [self.allow_ssh_str, self.default_deny_str,
               self.deny_out_to_any_str]
        self.start_firewall(cmd)

    def allow_all_incoming_and_outgoing(self):
        cmd = [self.delete_ssh_str, self.default_allow_str,
               self.delete_deny_out_to_any_str]
        self.stop_firewall(cmd)

    def deny_all_incoming_except_ssh(self):
        cmd = [self.allow_ssh_str, self.default_deny_str]
        self.start_firewall(cmd)

    def allow_all_incoming(self):
        cmd = [self.delete_ssh_str, self.default_allow_str]
        self.stop_firewall(cmd)

    def deny_all_outgoing_except_ssh(self):
        cmd = [self.allow_ssh_str, self.deny_out_to_any_str]
        self.start_firewall(cmd)

    def allow_all_outgoing(self):
        cmd = [self.delete_ssh_str, self.delete_deny_out_to_any_str]
        self.stop_firewall(cmd)

    def deny_port(self, port):
        cmd = 'ufw deny %s' % port
        self.start_firewall(cmd)

    def allow_port(self, port):
        cmd = 'ufw delete deny %s' % port
        self.stop_firewall(cmd)

    def deny_state_server(self):
        self.deny_port(37017)

    def allow_state_server(self):
        self.allow_port(37017)

    def deny_api_server(self):
        self.deny_port(17070)

    def allow_api_server(self):
        self.allow_port(17070)

    def deny_sys_log(self):
        self.deny_port(6514)

    def allow_sys_log(self):
        self.allow_port(6514)

    def enable_ufw(self):
        cmd = 'ufw --force enable'
        run_shell_command(cmd)

    def disable_ufw(self):
        cmd = 'ufw disable'
        run_shell_command(cmd)

    def start_firewall(self, commands):
        self.run_command(self.default_allow_str)
        self.run_command(commands)
        self.enable_ufw()

    def stop_firewall(self, command):
        self.run_command(command)
        self.disable_ufw()

    def run_command(self, command):
        commands = [command] if type(command) is str else command
        for cmd in commands:
            run_shell_command(cmd)

    def get_chaos(self):
        chaos = list()
        chaos.append(
            self.create_chaos(
                self.deny_all_incoming_and_outgoing_except_ssh,
                self.allow_all_incoming_and_outgoing, 'deny-all',
                'Deny all incoming and outgoing network traffic except ssh.'))
        chaos.append(
            self.create_chaos(
                self.deny_all_incoming_except_ssh, self.allow_all_incoming,
                'deny-incoming',
                'Deny all incoming network traffic except ssh.'))
        chaos.append(
            self.create_chaos(
                self.deny_all_outgoing_except_ssh, self.allow_all_outgoing,
                'deny-outgoing',
                'Deny all outgoing network traffic except ssh.'))
        chaos.append(
            self.create_chaos(
                self.deny_state_server, self.allow_state_server,
                'deny-state-server',
                'Deny network traffic to the Juju State-Server'))
        chaos.append(
            self.create_chaos(
                self.deny_api_server, self.allow_api_server,
                'deny-api-server',
                'Deny network traffic to the Juju API Server.'))
        chaos.append(
            self.create_chaos(
                self.deny_sys_log, self.allow_sys_log, 'deny-sys-log',
                'Deny network traffic to the Juju SysLog.'))
        return chaos

    def create_chaos(self, enable, disable, command_str, description):
        return Chaos(enable=enable, disable=disable, group=self.group,
                     command_str=command_str, description=description)

    def shutdown(self):
        self.reset()
