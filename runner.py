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
    NotFound,
    setup_logging,
    split_arg_string,
)


class Runner:
    def __init__(self, workspace, chaos_monkey, log_count=1, dry_run=False):
        self.workspace = workspace
        self.log_count = log_count
        self.dry_run = dry_run
        self.stop_chaos = False
        self.workspace_lock = False
        self.lock_file = '{}/{}'.format(self.workspace, 'chaos_runner.lock')
        self.chaos_monkey = chaos_monkey

    @classmethod
    def factory(cls, workspace, log_count=1, dry_run=False):
        log_dir_path = os.path.join(workspace, 'log')
        ensure_dir(log_dir_path)
        log_file = os.path.join(log_dir_path, 'results.log')
        setup_logging(log_path=log_file, log_count=log_count)
        chaos_monkey = ChaosMonkey.factory()
        return cls(workspace, chaos_monkey, log_count, dry_run)

    def acquire_lock(self):
        if not os.path.isdir(self.workspace):
            sys.stderr.write('Not a directory: {}\n'.format(self.workspace))
            sys.exit(-1)
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
        self.workspace_lock = True
        self.verify_lock()

    def verify_lock(self):
        if not self.workspace_lock:
            raise NotFound("Workspace is not locked.")
        with open(self.lock_file, 'r') as lock_file:
            pid = lock_file.read()
        expected_pid = str(os.getpid())
        if pid != expected_pid:
            raise NotFound('Unexpected pid: {} in {}, expected: {}'.format(
                pid, self.lock_file, expected_pid))

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

        self.filter_commands(include_group=include_group,
                             exclude_group=exclude_group,
                             include_command=include_command,
                             exclude_command=exclude_command)
        expire_time = time() + run_timeout
        while time() < expire_time:
            if self.stop_chaos or self.dry_run:
                break
            self.chaos_monkey.run_random_chaos(enablement_timeout)
        if not self.dry_run:
            self.chaos_monkey.shutdown()

    def cleanup(self):
        if self.lock_file:
            try:
                os.unlink(self.lock_file)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
                logging.warning('Lock file not found: {}'.format(
                    self.lock_file))
        logging.info('Chaos monkey stopped')

    def filter_commands(self, include_group=None, exclude_group=None,
                        include_command=None, exclude_command=None):
        # If any groups and any commands are not included, assume the intent
        #  is to include all groups and all commands.
        if not include_group and not include_command:
            self.chaos_monkey.include_group('all')
        if include_group:
            include_group = split_arg_string(include_group)
            self.chaos_monkey.include_group(include_group)
        if exclude_group:
            exclude_group = split_arg_string(exclude_group)
            self.chaos_monkey.exclude_group(exclude_group)
        if include_command:
            include_command = split_arg_string(include_command)
            self.chaos_monkey.include_command(include_command)
        if exclude_command:
            exclude_command = split_arg_string(exclude_command)
            self.chaos_monkey.exclude_command(exclude_command)

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
    runner = Runner.factory(workspace=args.path, log_count=args.log_count,
                            dry_run=args.dry_run)
    setup_sig_handlers(runner.sig_handler)
    runner.acquire_lock()
    logging.info('Chaos monkey started in {}'.format(args.path))
    logging.debug('Dry run is set to {}'.format(args.dry_run))
    runner.random_chaos(run_timeout=args.total_timeout,
                        enablement_timeout=args.enablement_timeout,
                        include_group=args.include_group,
                        exclude_group=args.exclude_group,
                        include_command=args.include_command,
                        exclude_command=args.exclude_command)
    runner.cleanup()
