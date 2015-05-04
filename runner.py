from argparse import ArgumentParser
import logging
from time import time

from chaos_monkey import ChaosMonkey
from utility import (
    BadRequest,
    setup_logging,
)


def random_chaos(run_timeout, enablement_timeout, include_group=None,
                 exclude_group=None, include_command=None,
                 exclude_command=None):
    """
    Runs a random_chaos chaos
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
        cm.run_random_chaos(enablement_timeout)
    cm.shutdown()


def filter_commands(chaos_monkey, include_group, exclude_group=None,
                    include_command=None, exclude_command=None):
    if not include_group or include_group == 'all':
        chaos_monkey.include_group('all')
    else:
        include_group = (include_group.split(',')
                         if ',' in include_group else [include_group])
        chaos_monkey.include_group(include_group)
    if exclude_group:
        exclude_group = (exclude_group.split(',')
                         if ',' in exclude_group else [exclude_group])
        chaos_monkey.exclude_group(exclude_group)
    if include_command:
        include_command = (include_command.split(',')
                           if ',' in include_command else [include_command])
        chaos_monkey.include_command(include_command)
    if exclude_command:
        exclude_command = (exclude_command.split(',')
                           if ',' in exclude_command else [exclude_command])
        chaos_monkey.exclude_command(exclude_command)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-pt', '--enablement-timeout', default=10, type=int,
        help="Enablement timeout in seconds")
    parser.add_argument(
        '-tt', '--total-timeout', default=60, type=int,
        help="Total timeout in seconds")
    parser.add_argument('-lp', '--log-path', help='Where to write logs.',
                        default='log/results.log')
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
    setup_logging(log_path=args.log_path, log_count=args.log_count)
    logging.info('Chaos monkey started')
    random_chaos(run_timeout=args.total_timeout,
                 enablement_timeout=args.enablement_timeout,
                 include_group=args.include_group,
                 exclude_group=args.exclude_group,
                 include_command=args.include_command,
                 exclude_command=args.exclude_command)
