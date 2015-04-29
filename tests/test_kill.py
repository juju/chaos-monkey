from unittest import TestCase

from mock import patch, call

from chaos.kill import Kill


class TestKill(TestCase):

    def test_get_pids(self):
        kill = Kill()
        with patch('utility.check_output', autospec=True,
                   return_value='1234 2345') as mock:
            pids = kill.get_pids('jujud')
        self.assertEqual(pids, ['1234', '2345'])
        mock.assert_called_once_with(['pidof', 'jujud'])

    def test_kill_jujud(self):
        kill = Kill()
        with patch('utility.check_output', autospec=True,
                   return_value='1234 2345') as mock:
            kill.kill_jujud()
        self.assertEqual(mock.mock_calls, [
            call(['pidof', 'jujud']),
            call(['kill', '-s', 'SIGKILL', '1234'])
        ])

    def test_kill_mongodb(self):
        kill = Kill()
        with patch('utility.check_output', autospec=True,
                   return_value='1234 2345') as mock:
            kill.kill_mongodb()
        self.assertEqual(mock.mock_calls, [
            call(['pidof', 'mongod']),
            call(['kill', '-s', 'SIGKILL', '1234'])
        ])

    def test_get_chaos(self):
        kill = Kill()
        chaos = kill.get_chaos()
        self.assertEqual(len(chaos), 2)
