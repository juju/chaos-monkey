from time import time
from unittest import TestCase

from mock import patch

from utility import BadRequest
from runner import random


class TestRunner(TestCase):

    def test_random(self):
        with patch('utility.check_output', autospec=True) as mock:
            random(run_timeout=1, enablement_timeout=1)
        self.assertEqual(mock.called, True)

    def test_random_enablement_zero(self):
        with patch('utility.check_output', autospec=True) as mock:
            random(run_timeout=1, enablement_timeout=0)
        self.assertEqual(mock.called, True)

    def test_random_raises_exception(self):
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    BadRequest,
                    "Total run timeout can't be less than enablement timeout"):
                random(run_timeout=1, enablement_timeout=2)

    def test_random_run_timeout_raises_exception_for_zero(self):
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    BadRequest, "Invalid value for run timeout"):
                random(run_timeout=0, enablement_timeout=-1)

    def test_random_run_timeout_raises_exception_for_less_than_zero(self):
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    BadRequest, "Invalid value for run timeout"):
                random(run_timeout=-1, enablement_timeout=-2)

    def test_random_run_enablement_raises_exception_for_less_than_zero(self):
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    BadRequest, "Invalid value for enablement timeout"):
                random(run_timeout=2, enablement_timeout=-1)

    def test_random_verify_timeout(self):
        run_timeout = 6
        with patch('utility.check_output', autospec=True) as mock:
            current_time = time()
            random(run_timeout=run_timeout, enablement_timeout=2)
            end_time = time()
        self.assertEqual(run_timeout, int(end_time-current_time))
        self.assertEqual(mock.called, True)

    def test_random_assert_chaos_monkey_methods_called(self):
        with patch('runner.ChaosMonkey', autospec=True) as cm_mock:
            random(run_timeout=1, enablement_timeout=1)
        cm_mock.factory.return_value.run_random_chaos.assert_called_with(1)
        cm_mock.factory.return_value.shutdown.assert_called_with()

    def test_random_assert_chaos_methods_called(self):
        net_ctx = patch('chaos.net.Net', autospec=True)
        kill_ctx = patch('chaos.kill.Kill', autospec=True)
        with patch('utility.check_output', autospec=True):
            with patch('chaos_monkey.ChaosMonkey.run_random_chaos',
                       autospec=True):
                with net_ctx as net_mock:
                    with kill_ctx as kill_mock:
                        random(run_timeout=1, enablement_timeout=1)
        net_mock.factory.return_value.shutdown.assert_called_with()
        kill_mock.factory.return_value.shutdown.assert_called_with()
        net_mock.factory.return_value.get_chaos.assert_called_with()
        kill_mock.factory.return_value.get_chaos.assert_called_with()

    def test_random_passes_timeout(self):
        with patch('utility.check_output', autospec=True):
            with patch('chaos_monkey.ChaosMonkey._run_command',
                       autospec=True) as mock:
                random(run_timeout=3, enablement_timeout=2)
        self.assertEqual(mock.call_args_list[0][1]['timeout'], 2)
