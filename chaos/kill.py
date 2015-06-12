# Copyright 2015 Canonical Ltd.
# Licensed under the AGPLv3, see LICENCE file for details.
import logging
from subprocess import CalledProcessError

from chaos_monkey_base import (
    Chaos,
    ChaosMonkeyBase,
)
from utility import (
    NotFound,
    run_shell_command,
)

__metaclass__ = type


class Kill(ChaosMonkeyBase):
    """Kill processes including shutting down a machine and restarting."""

    jujud_cmd = 'kill-jujud'
    mongod_cmd = 'kill-mongod'
    restart_cmd = 'restart-unit'
    group = 'kill'

    def __init__(self):
        super(Kill, self).__init__()

    @classmethod
    def factory(cls):
        return cls()

    def get_pids(self, process):
        """Return a list of process IDs."""
        pids = run_shell_command('pidof ' + process, quiet_mode=True)
        if not pids:
            return None
        return pids.strip().split(' ')

    def kill_jujud(self, quiet_mode=True):
        """Kill a jujud process.

        :param quiet_mode: When False, generates an exception on error.
        """
        pids = self.get_pids('jujud')
        if not pids:
            logging.error("Jujud process ID not found")
            if not quiet_mode:
                raise NotFound('Process id not found')
            return
        run_shell_command('kill -s SIGKILL ' + pids[0])

    def kill_mongodb(self, quiet_mode=True):
        """Kill mongod process.

        :param quiet_mode: When False, generates an exception on error.
        """
        pids = self.get_pids('mongod')
        if not pids:
            logging.error("MongoDB process ID not found")
            if not quiet_mode:
                raise NotFound('Process id not found')
            return
        run_shell_command('kill -s SIGKILL ' + pids[0])

    def restart_unit(self, quiet_mode=False):
        """Reboot the unit at the operating system level.

        :param quiet_mode: When False, generates an exception on error.
        """
        try:
            run_shell_command('shutdown -r now')
        except CalledProcessError:
            logging.error("Error while executing command: shutdown -r now ")
            if not quiet_mode:
                raise

    def get_chaos(self):
        """Return all available commands for the kill group."""
        chaos = list()
        chaos.append(
            Chaos(
                enable=self.kill_jujud,
                disable=None,
                group=self.group,
                command_str=self.jujud_cmd,
                description='Kill jujud process.'))
        chaos.append(
            Chaos(
                enable=self.kill_mongodb,
                disable=None,
                group=self.group,
                command_str=self.mongod_cmd,
                description='Kill mongod process.'))
        chaos.append(
            Chaos(
                enable=self.restart_unit,
                disable=None,
                group=self.group,
                command_str=self.restart_cmd,
                description='Restart the unit.'))
        return chaos
