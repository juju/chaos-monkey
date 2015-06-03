import os
from tempfile import NamedTemporaryFile

from unittest import TestCase

from utils.init import Init

__metaclass__ = type


class TestInit(TestCase):

    def test_upstart(self):
        init = Init.upstart()
        self.assertIsInstance(init, Init)
        self.assertEqual(init.init_path, '/etc/init/chaos-monkey-restart.conf')
        cm_dir = get_chaos_monkey_dir()
        self.assertEqual(init.init_script_path, os.path.join(
            cm_dir, 'scripts', 'chaos-monkey-restart.conf'))
        self.assertEqual(init.restart_script_path, os.path.join(
            cm_dir, 'scripts', 'restart_chaos_monkey.py'))
        self.assertEqual(init.runner_path, os.path.join(
            cm_dir, 'runner.py'))

    def test_install(self):
        init_script_path = os.path.join(
            get_chaos_monkey_dir(), 'scripts', 'chaos-monkey-restart.conf')
        with open(init_script_path) as f:
            conf_content = f.read()
        with NamedTemporaryFile() as init_fd:
            restart_script_path = '/scripts/restart_chaos_monkey.py'
            runner_path = '/path/runner.py'
            init = Init(init_path=init_fd.name,
                        init_script_path=init_script_path,
                        restart_script_path=restart_script_path,
                        runner_path=runner_path)
            cmd_arg = '--include-command=deny-all workspace'
            expire_time = 65537.00
            init.install(cmd_arg, expire_time)

            conf_content = conf_content.format(
                restart_script_path=restart_script_path,
                runner_path=runner_path,
                expire_time=expire_time,
                cmd_arg=cmd_arg)

            with open(init_fd.name) as f:
                init_content = f.read()
            self.assertEqual(init_content, conf_content)

    def test_uninstall(self):
        with NamedTemporaryFile(delete=False) as init_fd:
            init_fd.write('fake')
            init_fd.flush()
            os.fsync(init_fd)
            init = Init(init_path=init_fd.name,
                        init_script_path='fake',
                        restart_script_path='fake',
                        runner_path='fake')
            init.uninstall()
            self.assertIs(os.path.isfile(init_fd.name), False)


def get_chaos_monkey_dir():
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
