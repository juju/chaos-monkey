# Copyright 2015 Canonical Ltd.
# Licensed under the AGPLv3, see LICENCE file for details.
import errno
import logging
import os

__metaclass__ = type


class Init:
    """Generate Upstart init script."""

    def __init__(self, init_path, init_script_path, restart_script_path,
                 runner_path):
        self.init_path = init_path
        self.init_script_path = init_script_path
        self.restart_script_path = restart_script_path
        self.runner_path = runner_path

    @classmethod
    def upstart(cls):
        dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        scripts_dir_path = os.path.join(dir, 'scripts')
        init_filename = 'chaos-monkey-restart.conf'
        # Full path to upstart conf file.
        init_path = os.path.join('/etc/init/', init_filename)
        # Full path to upstart script file.
        # This file contains upstart conf script.
        init_script_path = os.path.join(scripts_dir_path,  init_filename)
        # Script filename that restarts the Chaos Monkey
        restart_script_filename = 'restart_chaos_monkey.py'
        # Full path to restart script file.
        restart_script_path = os.path.join(scripts_dir_path,
                                           restart_script_filename)
        runner_path = os.path.join(dir, 'runner.py')
        return cls(
            init_path, init_script_path, restart_script_path, runner_path)

    def install(self, cmd_arg, expire_time):
        """Install an Upstart script in the /etc/init directory."""
        cmd_arg = Init._remove_args(cmd_arg=cmd_arg)
        with open(self.init_script_path, 'r') as f:
            data = f.read().format(
                restart_script_path=self.restart_script_path,
                runner_path=self.runner_path,
                cmd_arg=cmd_arg,
                expire_time=expire_time,
            )
        # Write to /etc/init dir
        with open(self.init_path, 'w') as f:
            f.write(data)
        logging.info("Init script generated:\n cmd: {} \n expire_time: {} \n "
                     "runner_path: {}".format(cmd_arg,  expire_time,
                                              self.runner_path))

    @staticmethod
    def _remove_args(cmd_arg):
        cmd_arg = cmd_arg.replace('--restart ', '').replace('--restart', '')
        if '--expire-time' in cmd_arg:
            cmd_list = cmd_arg.split()
            remove_index = cmd_list.index('--expire-time')
            # Delete --expire-time
            del cmd_list[remove_index]
            # Delete expire-time's argument, which is the next item in the
            # list. "remove_index" is going to be the same because an item has
            # been removed and the size has been reduced.
            del cmd_list[remove_index]
            cmd_arg = ' '.join(cmd_list)
        return cmd_arg

    def uninstall(self):
        """Remove the Upstart script from /etc/init directory."""
        try:
            os.remove(self.init_path)
            logging.info("Init script removed from {}".format(self.init_path))
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
