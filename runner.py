from argparse import ArgumentParser
import logging
from time import time

from chaos_monkey import ChaosMonkey
from utility import (
    BadRequest,
    setup_logging,
)


def random(run_timeout, enablement_timeout):
    """
    Runs a random chaos
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
    expire_time = time() + run_timeout
    while time() < expire_time:
        cm.run_random_chaos(enablement_timeout)
    cm.shutdown()


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
    args = parser.parse_args()
    setup_logging(log_path=args.log_path, log_count=args.log_count)
    logging.info('Chaos monkey started')
    random(run_timeout=args.total_timeout,
           enablement_timeout=args.enablement_timeout)
