import errno
import os


__metaclass__ = type


class Init:

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
        cmd_arg = cmd_arg.replace('--restart ', '').replace(
            '--expire-time ', '')
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

    def uninstall(self):
        try:
            os.remove(self.init_path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
