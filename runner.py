from argparse import ArgumentParser
import errno
import logging
import os
import signal
import sys
from time import time

from chaos_monkey import ChaosMonkey
from utility import (
    BadRequest,
    ensure_dir,
    setup_logging,
    split_arg_string,
)

stop_chaos = False
lock_fd = None
lock_file = None


class Runner:
    def __init__(self, workspace, log_count, dry_run=False):
        self.stop_chaos = False
        self.workspace = workspace
        self.aquire_lock()
        self.dry_run = dry_run
        log_dir_path = os.path.join(self.workspace, 'log')
        ensure_dir(log_dir_path)
        log_file = os.path.join(log_dir_path, 'results.log')
        setup_logging(log_path=log_file, log_count=log_count)

    def aquire_lock(self):
        if not os.path.isdir(self.workspace):
            sys.stderr.write('Not a directory: {}\n'.format(self.workspace))
            sys.exit(-1)
        self.lock_file = '{}/{}'.format(self.workspace, 'chaos_runner.lock')
        try:
            lock_fd = os.open(self.lock_file,
                              os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except OSError as e:
            if e.errno == errno.EEXIST:
                sys.stderr.write('Lock file already exists: {}\n'.format(
                    self.lock_file))
            sys.exit(-1)
        os.write(lock_fd, str(os.getpid()))
        os.fsync(lock_fd)
        os.close(lock_fd)

    def random_chaos(self, run_timeout, enablement_timeout, include_group=None,
                     exclude_group=None, include_command=None,
                     exclude_command=None):
        """Runs a random chaos monkey

        :param run_timeout: Total time to run the chaos
        :param enablement_timeout: Time between enabling and disabling chaos.
        Example: disable all the network, wait for timeout and enable it back
        :rtype none
        """
        if enablement_timeout > run_timeout:
            raise BadRequest(
                "Total run timeout can't be less than enablement timeout")
        if run_timeout <= 0:
            raise BadRequest("Invalid value for run timeout")
        if enablement_timeout < 0:
            raise BadRequest("Invalid value for enablement timeout")

        cm = ChaosMonkey.factory()
        self.filter_commands(
            chaos_monkey=cm, include_group=include_group,
            exclude_group=exclude_group, include_command=include_command,
            exclude_command=exclude_command)
        expire_time = time() + run_timeout
        while time() < expire_time:
            if self.stop_chaos:
                break
            if not self.dry_run:
                logging.debug('BOOM')
                # cm.run_random_chaos(enablement_timeout)
        if not self.dry_run:
            cm.shutdown()

    def cleanup(self):
        if self.lock_file:
            os.unlink(self.lock_file)
        logging.info('Chaos monkey stopped')

    def filter_commands(self, chaos_monkey, include_group, exclude_group=None,
                        include_command=None, exclude_command=None):
        if not include_group or include_group == 'all':
            chaos_monkey.include_group('all')
        else:
            include_group = split_arg_string(include_group)
            chaos_monkey.include_group(include_group)
        if exclude_group:
            exclude_group = split_arg_string(exclude_group)
            chaos_monkey.exclude_group(exclude_group)
        if include_command:
            include_command = split_arg_string(include_command)
            chaos_monkey.include_command(include_command)
        if exclude_command:
            exclude_command = split_arg_string(exclude_command)
            chaos_monkey.exclude_command(exclude_command)

    def sig_handler(self, sig_num, frame):
        """Set the stop_chaos flag, to request a safe exit."""
        logging.info('Caught signal {}: Waiting for graceful exit.\n'.format(
                     sig_num))
        logging.debug('Flagging stop for runner in workspace: {}'.format(
                      self.workspace))
        self.stop_chaos = True
        logging.debug('self.stop_chaos: {}'.format(self.stop_chaos))


def setup_sig_handlers(handler):
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'path',
        help='An existing directory, to be used as a workspace.')
    parser.add_argument(
        '-pt', '--enablement-timeout', default=10, type=int,
        help="Enablement timeout in seconds")
    parser.add_argument(
        '-tt', '--total-timeout', default=60, type=int,
        help="Total timeout in seconds")
    parser.add_argument(
        '-lc', '--log-count', default=2, type=int,
        help='The number of backups to keep.')
    parser.add_argument(
        '-ig', '--include-group',
        help='Include these groups only in the test')
    parser.add_argument(
        '-eg', '--exclude-group',
        help='Exclude groups from the test')
    parser.add_argument(
        '-ic', '--include-command',
        help='Include commands in test.')
    parser.add_argument(
        '-ec', '--exclude-command',
        help='Exclude commands in the test')
    parser.add_argument(
        '-dr', '--dry-run', dest='dry_run', action='store_true',
        help='Do not actually run chaos operations.')
    args = parser.parse_args()
    runner = Runner(args.path, args.log_count, dry_run=args.dry_run)
    setup_sig_handlers(runner.sig_handler)
    logging.info('Chaos monkey started in {}'.format(args.path))
    logging.debug('Dry run is set to {}'.format(args.dry_run))
    runner.random_chaos(run_timeout=args.total_timeout,
                        enablement_timeout=args.enablement_timeout,
                        include_group=args.include_group,
                        exclude_group=args.exclude_group,
                        include_command=args.include_command,
                        exclude_command=args.exclude_command)
    runner.cleanup()
