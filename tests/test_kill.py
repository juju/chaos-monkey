from subprocess import CalledProcessError

from mock import patch, call

from chaos.kill import Kill
from tests.common_test_base import CommonTestBase


class TestKill(CommonTestBase):

    def setUp(self):
        self.setup_test_logging()

    def test_get_pids(self):
        kill = Kill()
        with patch('utility.check_output', autospec=True,
                   return_value='1234 2345\n') as mock:
            pids = kill.get_pids('jujud')
        self.assertEqual(pids, ['1234', '2345'])
        mock.assert_called_once_with(['pidof', 'jujud'])

    def test_get_pids_no_process(self):
        kill = Kill()
        with patch('utility.check_output', autospec=True,
                   side_effect=CalledProcessError(1, 'pidof fake')) as mock:
            pids = kill.get_pids('fake')
        self.assertEqual(pids, None)
        mock.assert_called_once_with(['pidof', 'fake'])

    def test_kill_jujud(self):
        kill = Kill()
        with patch('utility.check_output', autospec=True,
                   return_value='1234 2345\n') as mock:
            kill.kill_jujud()
        self.assertEqual(mock.mock_calls, [
            call(['pidof', 'jujud']),
            call(['kill', '-s', 'SIGKILL', '1234'])
        ])

    def test_kill_jujud_single_process(self):
        kill = Kill()
        with patch('utility.check_output', autospec=True,
                   return_value='2345\n') as mock:
            kill.kill_jujud()
        self.assertEqual(mock.mock_calls, [
            call(['pidof', 'jujud']),
            call(['kill', '-s', 'SIGKILL', '2345'])
        ])

    def test_kill_mongodb(self):
        kill = Kill()
        with patch('utility.check_output', autospec=True,
                   return_value='1234 2345\n') as mock:
            kill.kill_mongodb()
        self.assertEqual(mock.mock_calls, [
            call(['pidof', 'mongod']),
            call(['kill', '-s', 'SIGKILL', '1234'])
        ])

    def test_kill_mongodb_single_process(self):
        kill = Kill()
        with patch('utility.check_output', autospec=True,
                   return_value='2345\n') as mock:
            kill.kill_mongodb()
        self.assertEqual(mock.mock_calls, [
            call(['pidof', 'mongod']),
            call(['kill', '-s', 'SIGKILL', '2345'])
        ])

    def test_get_chaos(self):
        kill = Kill()
        chaos = kill.get_chaos()
        self.assertItemsEqual(
            self.get_command_str(chaos), get_all_kill_commands())

    def test_get_chaos_verify_method_calls(self):
        kill = Kill()
        chaos = kill.get_chaos()
        for c in chaos:
            if c.command_str == 'mongod':
                self.assertEqual(c.enable, kill.kill_mongodb)
            if c.command_str == 'jujud':
                self.assertEqual(c.enable, kill.kill_jujud)
            self.assertEqual(c.group, 'kill')
            self.assertEqual(c.disable, None)

    def test_restart_node(self):
        kill = Kill()
        with patch('utility.check_output') as mock:
            kill.restart_unit()
        mock.assert_called_once_with(['shutdown', '-r', 'now'])


def get_all_kill_commands():
    return ['jujud', 'mongod']
