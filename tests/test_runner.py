from time import time

from mock import patch

from chaos_monkey import ChaosMonkey
from chaos_monkey_base import Chaos
from runner import (
    random_chaos,
    filter_commands,
    split_arg_string,
)
from tests.test_chaos_monkey import CommonTestBase
from utility import BadRequest

__metaclass__ = type


class TestRunner(CommonTestBase):

    def test_random(self):
        with patch('utility.check_output', autospec=True) as mock:
            random_chaos(run_timeout=1, enablement_timeout=1)
        self.assertEqual(mock.called, True)

    def test_random_enablement_zero(self):
        with patch('utility.check_output', autospec=True) as mock:
            random_chaos(run_timeout=1, enablement_timeout=0)
        self.assertEqual(mock.called, True)

    def test_random_raises_exception(self):
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    BadRequest,
                    "Total run timeout can't be less than enablement timeout"):
                random_chaos(run_timeout=1, enablement_timeout=2)

    def test_random_run_timeout_raises_exception_for_zero(self):
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    BadRequest, "Invalid value for run timeout"):
                random_chaos(run_timeout=0, enablement_timeout=-1)

    def test_random_run_timeout_raises_exception_for_less_than_zero(self):
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    BadRequest, "Invalid value for run timeout"):
                random_chaos(run_timeout=-1, enablement_timeout=-2)

    def test_random_run_enablement_raises_exception_for_less_than_zero(self):
        with patch('utility.check_output', autospec=True):
            with self.assertRaisesRegexp(
                    BadRequest, "Invalid value for enablement timeout"):
                random_chaos(run_timeout=2, enablement_timeout=-1)

    def test_random_verify_timeout(self):
        run_timeout = 6
        with patch('utility.check_output', autospec=True) as mock:
            current_time = time()
            random_chaos(run_timeout=run_timeout, enablement_timeout=2)
            end_time = time()
        self.assertEqual(run_timeout, int(end_time-current_time))
        self.assertEqual(mock.called, True)

    def test_random_assert_chaos_monkey_methods_called(self):
        with patch('runner.ChaosMonkey', autospec=True) as cm_mock:
            random_chaos(run_timeout=1, enablement_timeout=1)
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
                        random_chaos(run_timeout=1, enablement_timeout=1)
        net_mock.factory.return_value.shutdown.assert_called_with()
        kill_mock.factory.return_value.shutdown.assert_called_with()
        net_mock.factory.return_value.get_chaos.assert_called_with()
        kill_mock.factory.return_value.get_chaos.assert_called_with()

    def test_random_passes_timeout(self):
        with patch('utility.check_output', autospec=True):
            with patch('chaos_monkey.ChaosMonkey._run_command',
                       autospec=True) as mock:
                random_chaos(run_timeout=3, enablement_timeout=2)
        self.assertEqual(mock.call_args_list[0][1]['timeout'], 2)

    def test_filter_commands_include_group_all(self):
        cm = ChaosMonkey.factory()
        include_group = 'all'
        filter_commands(cm, include_group=include_group,
                        exclude_group=None)
        self.verify_equals_to_all_chaos(cm.chaos)

    def test_filter_commands_include_group_none(self):
        cm = ChaosMonkey.factory()
        include_group = None
        filter_commands(cm, include_group=include_group,
                        exclude_group=None)
        self.verify_equals_to_all_chaos(cm.chaos)

    def test_filter_commands_include_groups(self):
        cm = ChaosMonkey.factory()
        include_group = 'net,kill'
        filter_commands(cm, include_group=include_group)
        self.assertGreaterEqual(len(cm.chaos), 2)
        self.assertTrue(
            all(c.group == 'net' or c.group == 'kill' for c in cm.chaos))

    def test_filter_commands_include_group(self):
        cm = ChaosMonkey.factory()
        include_group = 'net'
        filter_commands(cm, include_group=include_group)
        self.assertGreaterEqual(len(cm.chaos), 2)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))

    def test_filter_commands_exclude_group(self):
        cm = ChaosMonkey.factory()
        exclude_group = 'net'
        filter_commands(cm, include_group='all', exclude_group=exclude_group)
        self.assertGreaterEqual(len(cm.chaos), 2)
        self.assertTrue(all(c.group != 'net' for c in cm.chaos))

    def test_filter_commands_exclude_groups(self):
        cm = ChaosMonkey.factory()
        exclude_groups = 'net,kill'
        filter_commands(cm, include_group='all', exclude_group=exclude_groups)
        add_fake_group(cm.chaos)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(
            all(c.group != 'net' and c.group != 'kill' for c in cm.chaos))
        self.assertTrue(any(c.group == 'fake_group' for c in cm.chaos))

    def test_filter_commands_include_and_exclude_groups(self):
        cm = ChaosMonkey.factory()
        include_group = 'net,kill'
        exclude_groups = 'kill'
        filter_commands(
            cm, include_group=include_group, exclude_group=exclude_groups)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))

    def test_filter_commands_include_group_and_include_command(self):
        cm = ChaosMonkey.factory()
        include_group = 'net'
        include_command = 'jujud'
        filter_commands(
            cm, include_group=include_group, include_command=include_command)
        self.assertGreaterEqual(len(cm.chaos), 2)
        self.assertTrue(any(c.group == 'net' for c in cm.chaos))
        self.assertTrue(any(c.group == 'kill' for c in cm.chaos))
        self.assertTrue(any(c.command_str == 'jujud' for c in cm.chaos))

    def test_filter_commands_include_group_and_include_commands(self):
        cm = ChaosMonkey.factory()
        include_group = 'net'
        include_command = 'jujud,mongod'
        filter_commands(
            cm, include_group=include_group, include_command=include_command)
        self.assertGreaterEqual(len(cm.chaos), 2)
        self.assertTrue(any(c.group == 'net' for c in cm.chaos))
        self.assertTrue(any(c.group == 'kill' for c in cm.chaos))
        self.assertTrue(any(c.command_str == 'jujud' for c in cm.chaos))
        self.assertTrue(any(c.command_str == 'mongod' for c in cm.chaos))

    def test_filter_commands_include_group_and_exclude_command(self):
        cm = ChaosMonkey.factory()
        include_group = 'net'
        exclude_command = 'deny-all'
        filter_commands(
            cm, include_group=include_group, exclude_command=exclude_command)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))
        self.assertTrue(all(c.command_str != 'deny-all' for c in cm.chaos))

    def test_filter_commands_include_group_and_exclude_commands(self):
        cm = ChaosMonkey.factory()
        include_group = 'net'
        exclude_command = 'deny-all,deny-ssh'
        filter_commands(
            cm, include_group=include_group, exclude_command=exclude_command)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(all(c.group == 'net' for c in cm.chaos))
        self.assertTrue(all(c.command_str != 'deny-all' for c in cm.chaos))
        self.assertTrue(all(c.command_str != 'deny-ssh' for c in cm.chaos))

    def test_filter_commands_exclude_group_and_exclude_commands(self):
        cm = ChaosMonkey.factory()
        include_group = 'all'
        exclude_group = 'kill'
        exclude_command = 'deny-all,jujud'
        filter_commands(
            cm, include_group=include_group, exclude_group=exclude_group,
            exclude_command=exclude_command)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(any(c.group != 'kill' for c in cm.chaos))
        self.assertTrue(all(c.command_str != 'deny-all' for c in cm.chaos))
        self.assertTrue(all(c.command_str != 'jujud' for c in cm.chaos))

    def test_filter_commands_exclude_groups_and_exclude_commands(self):
        cm = ChaosMonkey.factory()
        include_group = 'all'
        exclude_group = 'kill,net'
        exclude_command = 'deny-all,jujud'
        filter_commands(
            cm, include_group=include_group, exclude_group=exclude_group,
            exclude_command=exclude_command)
        add_fake_group(cm.chaos)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(any(c.group == 'fake_group' for c in cm.chaos))
        self.assertTrue(any(c.group != 'kill' for c in cm.chaos))
        self.assertTrue(any(c.group != 'net' for c in cm.chaos))
        self.assertTrue(all(c.command_str != 'deny-all' for c in cm.chaos))
        self.assertTrue(all(c.command_str != 'jujud' for c in cm.chaos))

    def test_filter_commands_include_exclude_group_and_command(self):
        cm = ChaosMonkey.factory()
        include_group = 'net,kill'
        exclude_group = 'kill'
        include_command = 'jujud'
        exclude_command = 'deny-all,monogd'
        filter_commands(
            cm, include_group=include_group, exclude_group=exclude_group,
            include_command=include_command, exclude_command=exclude_command)
        add_fake_group(cm.chaos)
        self.assertGreaterEqual(len(cm.chaos), 1)
        self.assertTrue(any(c.group == 'net' for c in cm.chaos))
        # Adding 'jujud' command automatically adds kill group but the only
        # command in kill group should be jujud
        self.assertTrue(any(
            c.group == 'kill' and c.command_str == 'jujud' for c in cm.chaos))
        self.assertTrue(all(c.command_str != 'deny-all' for c in cm.chaos))
        self.assertTrue(all(c.command_str != 'mongod' for c in cm.chaos))

    def test_filter_commands_gets_options_from_random_chaos(self):
        with patch('runner.ChaosMonkey', autospec=True) as cm_mock:
            with patch('runner.filter_commands', autospec=True) as f_mock:
                random_chaos(
                    run_timeout=1, enablement_timeout=1,
                    include_group='net,kill', exclude_group='kill',
                    include_command='deny-all',  exclude_command='deny-ssh')

        cm_mock.factory.return_value.run_random_chaos.assert_called_with(1)
        cm_mock.factory.return_value.shutdown.assert_called_with()
        f_mock.assert_called_once_with(
            chaos_monkey=cm_mock.factory.return_value,
            include_group='net,kill', exclude_group='kill',
            include_command='deny-all',  exclude_command='deny-ssh')

    def test_split_arg_string(self):
        arg = split_arg_string('net,kill')
        self.assertItemsEqual(arg, ['net', 'kill'])
        arg = split_arg_string('net')
        self.assertItemsEqual(arg, ['net'])


def add_fake_group(chaos_monkey):
    chaos = Chaos(None, None, 'fake_group', 'fake_command_str', 'description')
    chaos_monkey.append(chaos)
