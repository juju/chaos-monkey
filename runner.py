from argparse import ArgumentParser, RawDescriptionHelpFormatter
import errno
import logging
import os
import random
import signal
import sys
from time import (
    time,
    sleep
)

from chaos.kill import Kill
from chaos_monkey import ChaosMonkey
from utility import (
    BadRequest,
    ensure_dir,
    NotFound,
    setup_logging,
    split_arg_string,
    StructuredMessage,
)
from utils.init import Init


class Runner:
    def __init__(self, workspace, chaos_monkey, log_count=1, dry_run=False,
                 cmd_log_name=None):
        self.workspace = workspace
        self.log_count = log_count
        self.dry_run = dry_run
        self.stop_chaos = False
        self.workspace_lock = False
        self.lock_file = '{}/{}'.format(self.workspace, 'chaos_runner.lock')
        self.chaos_monkey = chaos_monkey
        self.expire_time = None
        self.cmd_log_name = cmd_log_name

    @classmethod
    def factory(cls, workspace, log_count=1, dry_run=False):
        log_dir_path = os.path.join(workspace, 'log')
        ensure_dir(log_dir_path)
        log_file = os.path.join(log_dir_path, 'results.log')
        cmd_log_file = os.path.join(log_dir_path, 'chaos_run_list.log')
        cmd_log_name = 'cmd_log'
        setup_logging(log_path=log_file, log_count=log_count)
        setup_logging(
            log_path=cmd_log_file, log_count=log_count,  name=cmd_log_name,
            add_stream=False, disable_formatter=True)
        chaos_monkey = ChaosMonkey.factory()
        return cls(workspace, chaos_monkey, log_count, dry_run, cmd_log_name)

    def acquire_lock(self, restart=False):
        if not os.path.isdir(self.workspace):
            sys.stderr.write('Not a directory: {}\n'.format(self.workspace))
            sys.exit(-1)
        init = Init.upstart()
        init.uninstall()
        try:
            file_flag = ((os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                         if not restart else (os.O_CREAT | os.O_WRONLY))
            lock_fd = os.open(self.lock_file, file_flag)
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
                     exclude_command=None, run_once=False, expire_time=None):
        """Runs a random chaos monkey."""
        self.filter_commands(
            include_group=include_group, exclude_group=exclude_group,
            include_command=include_command, exclude_command=exclude_command)
        self.expire_time = expire_time or (time() + run_timeout)
        while time() < self.expire_time:
            if self.stop_chaos or self.dry_run:
                break
            self._run_command(enablement_timeout)
            if run_once:
                break

    def _run_command(self, enablement_timeout):
        chaos = random.choice(self.chaos_monkey.chaos)
        logging.info("{}".format(chaos.description))
        cmd_logger = logging.getLogger(self.cmd_log_name)
        cmd_logger.info(StructuredMessage(
            chaos.command_str, enablement_timeout))
        if chaos.command_str == Kill.restart_cmd:
            self.stop_chaos = True
            init = Init.upstart()
            init.install(
                cmd_arg=' '.join(sys.argv[1:]), expire_time=self.expire_time)
        chaos.enable()
        if chaos.command_str == Kill.restart_cmd:
            return

        sleep(enablement_timeout)
        if chaos.disable:
            chaos.disable()

    def cleanup(self, restart=False):
        if self.lock_file:
            try:
                os.unlink(self.lock_file)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
                if not restart:
                    logging.warning('Lock file not found: {}'.format(
                        self.lock_file))
        logging.info('Chaos Monkey stopped.\n')

    def filter_commands(self, include_group=None, exclude_group=None,
                        include_command=None, exclude_command=None):
        all_groups = ChaosMonkey.get_all_groups()
        all_commands = ChaosMonkey.get_all_commands()

        # If any groups and any commands are not included, assume the intent
        #  is to include all groups and all commands.
        if not include_group and not include_command:
            self.chaos_monkey.include_group('all')
        if include_group:
            include_group = self._validate(include_group, all_groups)
            self.chaos_monkey.include_group(include_group)
        if exclude_group:
            exclude_group = self._validate(exclude_group, all_groups)
            self.chaos_monkey.exclude_group(exclude_group)
        if include_command:
            include_command = self._validate(
                include_command, all_commands)
            self.chaos_monkey.include_command(include_command)
        if exclude_command:
            exclude_command = self._validate(
                exclude_command, all_commands)
            self.chaos_monkey.exclude_command(exclude_command)

    @staticmethod
    def _validate(sub_string, all_list):
        sub_list = split_arg_string(sub_string)
        for item in sub_list:
            if item not in all_list:
                raise BadRequest(
                    'Invalid value given on command line: {}'.format(item))
        return sub_list

    def sig_handler(self, sig_num, frame):
        """Set the stop_chaos flag, to request a safe exit."""
        logging.info('Caught signal {}: Waiting for graceful exit.\n'.format(
                     sig_num))
        logging.debug('Flagging stop for runner in workspace: {}'.format(
                      self.workspace))
        self.stop_chaos = True
        logging.debug('self.stop_chaos: {}'.format(self.stop_chaos))

    @staticmethod
    def list_all_commands():
        all_chaos, _ = ChaosMonkey.get_all_chaos()
        all_groups = ChaosMonkey.get_all_groups()
        commands = {}
        for group in all_groups:
            commands[group] = [[c.command_str, c.description]
                               for c in all_chaos if c.group == group]
        return commands


def setup_sig_handlers(handler):
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


def display_all_commands():
    commands = Runner.list_all_commands()
    groups = commands.keys()
    cmd_str = 'GROUP:  a comma-separated list of group names.\n'
    cmd_str += '  Valid groups: {}\n\n'.format(', '.join(groups))
    cmd_str += 'COMMANDS:  a comma-separated list of chaos commands:\n'
    for group, values in commands.iteritems():
        cmd_str += "  Group: " + group + "\n"
        for value in values:
            cmd_str += "     " + value[0] + ": " + value[1] + "\n"
        cmd_str += "\n"
    return cmd_str


def parse_args(argv=None):
    commands = display_all_commands()
    parser = ArgumentParser(
        description="Run Chaos Monkey.",  usage="[OPTIONS] path",
        epilog=commands, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument(
        'path', help='An existing directory, to be used as a workspace.')
    parser.add_argument(
        '-et', '--enablement-timeout', default=10, type=int,
        help="Enablement timeout in seconds.", metavar='SECONDS')
    parser.add_argument(
        '-tt', '--total-timeout', type=int, help="Total timeout in seconds.",
        metavar='SECONDS')
    parser.add_argument(
        '-lc', '--log-count', default=2, type=int, metavar='NUMBER',
        help='The number of backups to keep.')
    parser.add_argument(
        '-ig', '--include-group', metavar='GROUP',
        help='Select chaos from only a specified group or set of groups. '
             'All groups are included by default.',
        default=None)
    parser.add_argument(
        '-eg', '--exclude-group', metavar='GROUP',
        help='Exclude a group or set of groups from selected chaos.',
        default=None)
    parser.add_argument(
        '-ic', '--include-command', metavar='COMMAND',
        help="Select chaos from only a specified command or set of commands. "
             "All commands are included by default.",
        default=None)
    parser.add_argument(
        '-ec', '--exclude-command', metavar='COMMAND',
        help='Exclude a command or set of commands from selected chaos.',
        default=None)
    parser.add_argument(
        '-dr', '--dry-run', dest='dry_run', action='store_true',
        help='Do not actually run chaos operations.', default=False)
    parser.add_argument(
        '-ro', '--run-once', action='store_true',
        help='Run a single command only.', default=False)
    parser.add_argument(
        '-r', '--restart', action='store_true',
        help='Indicates the run is after a reboot.', default=False)
    parser.add_argument(
        '-ep', '--expire-time', type=float,
        help='Chaos Monkey expire time (UNIX timestamp).', default=None)
    args = parser.parse_args(argv)

    if args.run_once and args.total_timeout:
        parser.error("Conflicting request: total-timeout is irrelevant "
                     "if run-once is set.")
    if not args.expire_time:
        if not args.total_timeout:
            args.total_timeout = args.enablement_timeout
        if args.enablement_timeout > args.total_timeout:
            parser.error("total-timeout can not be less than "
                         "enablement-timeout.")
        if args.total_timeout <= 0:
            parser.error("Invalid total-timeout value: timeout must be "
                         "greater than zero.")
    if args.enablement_timeout < 0:
        parser.error("Invalid enablement-timeout value: timeout must be "
                     "zero or greater.")
    return args

if __name__ == '__main__':
    args = parse_args()
    runner = Runner.factory(workspace=args.path, log_count=args.log_count,
                            dry_run=args.dry_run)
    setup_sig_handlers(runner.sig_handler)
    msg = 'started' if not args.restart else 'restarted after a reboot'
    logging.info('Chaos Monkey {} in {}'.format(msg, args.path))
    logging.debug('Dry run is set to {}'.format(args.dry_run))
    if args.run_once and args.restart:
        runner.cleanup(restart=True)
        sys.exit(0)

    runner.acquire_lock(restart=args.restart)
    try:
        runner.random_chaos(
            run_timeout=args.total_timeout,
            enablement_timeout=args.enablement_timeout,
            include_group=args.include_group,
            exclude_group=args.exclude_group,
            include_command=args.include_command,
            exclude_command=args.exclude_command,
            run_once=args.run_once,
            expire_time=args.expire_time)
    except Exception as e:
        logging.error('{} ({})'.format(e, type(e).__name__))
        sys.exit(1)
    finally:
        runner.cleanup()
