from subprocess import CalledProcessError
from unittest import TestCase

from mock import patch

from utility import run_shell_command


class TestUtility(TestCase):

    def test_run_shell_command(self):
        with patch('utility.check_output', autospec=True) as mock:
            run_shell_command('foo')
        mock.assert_called_once_with(['foo'])

    def test_run_shell_command_error(self):
        with self.assertRaisesRegexp(CalledProcessError, ""):
            run_shell_command('ls -W', quiet_mode=False)

    def test_run_shell_command_output(self):
        output = run_shell_command('echo "hello"')
        self.assertEqual(output, '"hello"\n')
