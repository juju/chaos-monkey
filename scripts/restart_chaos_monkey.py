from argparse import ArgumentParser
from subprocess import (
    CalledProcessError,
    check_output,
)
import sys


def parse_args(argv=None):
    parser = ArgumentParser()
    parser.add_argument(
        '--runner-path',  help='Chaos Monkey runner path.',  default=None)
    parser.add_argument(
        '--expire-time',  help='Chaos Monkey expire time.',  default=None,
        type=float)
    parser.add_argument(
        '--cmd-arg',  help='Chaos Monkey command arguments.',  default=None)
    args = parser.parse_args(argv)
    if not args.runner_path or not args.expire_time or not args.cmd_arg:
        parser.error("Invalid command arguments.")
    return args


def restart_chaos_monkey(args):
    cmd = ([args.runner_path] + args.cmd_arg.split(' ') +
           ['--expire-time'] + [args.expire_time] + ['--restart'])

    try:
        check_output(cmd)
    except CalledProcessError:
        sys.stderr.write(
            'Cloud not restart Chaos Monkey. cmd:{}'.format(args.cmd_arg))
        sys.exit(-1)

if __name__ == '__main__':
    args = parse_args()
    restart_chaos_monkey(args)
