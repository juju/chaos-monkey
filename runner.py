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
)

STOP_CHAOS = False
LOCK_FD = None
LOCK_FILE = None


def aquire_lock(workspace):
    if not os.path.isdir(workspace):
        sys.stderr.write('Not a directory: {}\n'.format(workspace))
        sys.exit(-1)
    global LOCK_FILE
    LOCK_FILE = '{}/{}'.format(workspace, 'chaos_runner.lock')
    try:
        global LOCK_FD
        LOCK_FD = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sys.stderr.write('Lock file already exists: {}\n'.format(
                LOCK_FILE))
        sys.exit(-1)
    os.write(LOCK_FD, str(os.getpid()))
    os.fsync(LOCK_FD)


def random_chaos(run_timeout, enablement_timeout, include_group=None,
                 exclude_group=None, include_command=None,
                 exclude_command=None):
    """ Runs a random chaos monkey

    :param run_timeout: Total time to run the chaos
    :param enablement_timeout: Timeout between enabling and disabling a chaos.
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
    filter_commands(
        chaos_monkey=cm, include_group=include_group,
        exclude_group=exclude_group, include_command=include_command,
        exclude_command=exclude_command)
    expire_time = time() + run_timeout
    while time() < expire_time:
        if STOP_CHAOS:
            break
        cm.run_random_chaos(enablement_timeout)
    cm.shutdown()


def cleanup():
    os.close(LOCK_FD)
    os.unlink(LOCK_FILE)
    logging.info('Chaos monkey stopped')


def setup_sig_handlers():
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)


def sig_handler(sig_num, frame):
    """Set the STOP_CHAOS flag, to request a safe exit."""
    logging.debug('Handling signal: {}'.format(sig_num))
    global STOP_CHAOS
    STOP_CHAOS = True
    cleanup()


def split_arg_string(arg_string):
    return arg_string.split(',') if ',' in arg_string else [arg_string]


def filter_commands(chaos_monkey, include_group, exclude_group=None,
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
    parser.add_argument('-lc', '--log-count', default=2, type=int,
                        help='The number of backups to keep.')
    parser.add_argument('-ig', '--include-group',
                        help='Include these groups only in the test')
    parser.add_argument('-eg', '--exclude-group',
                        help='Exclude groups from the test')
    parser.add_argument(
        '-ic', '--include-command', help='Include commands in test.')
    parser.add_argument(
        '-ec', '--exclude-command', help='Exclude commands in the test')
    args = parser.parse_args()
    aquire_lock(workspace=args.path)
    log_dir_path = os.path.join(args.path, 'log')
    ensure_dir(log_dir_path)
    log_file = os.path.join(log_dir_path, 'results.log')
    setup_logging(log_path=log_file, log_count=args.log_count)
    logging.info('Chaos monkey started in {}'.format(args.path))
    random_chaos(run_timeout=args.total_timeout,
                 enablement_timeout=args.enablement_timeout,
                 include_group=args.include_group,
                 exclude_group=args.exclude_group,
                 include_command=args.include_command,
                 exclude_command=args.exclude_command)
    cleanup()
