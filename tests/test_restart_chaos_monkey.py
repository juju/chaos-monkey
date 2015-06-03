from argparse import Namespace

from mock import patch
from unittest import TestCase

from scripts.restart_chaos_monkey import (
    parse_args,
    restart_chaos_monkey,
)

__metaclass__ = type


class TestRestartChaosMonkey(TestCase):

    def test_parse_args(self):
        args = parse_args([
            '--runner-path', '/path/runner.py',
            '--expire-time', '123.00',
            '--cmd-arg', '--include-command deny-all workspace'])
        self.assertEqual(args, Namespace(
            runner_path='/path/runner.py',
            expire_time=123.00,
            cmd_arg='--include-command deny-all workspace'))

    def test_execute_chaos_monkey(self):
        args = parse_args([
            '--runner-path', '/path/runner.py',
            '--expire-time', '123.0',
            '--cmd-arg', '--include-command deny-all workspace'])
        with patch('scripts.restart_chaos_monkey.check_output',
                   autospec=True) as mock:
            restart_chaos_monkey(args)
        mock.assert_called_once_with([
            '/path/runner.py', '--include-command', 'deny-all', 'workspace',
            '--expire-time', 123.0, '--restart'])
