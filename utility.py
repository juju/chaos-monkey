from __future__ import print_function

from subprocess import (
    CalledProcessError,
    check_output,
)


def run_shell_command(cmd, quiet_mode=True):
    shell_cmd = cmd.split(' ') if type(cmd) is str else cmd
    output = None
    try:
        output = check_output(shell_cmd)
    except CalledProcessError:
        log("Command generated error: %s " % cmd)
        if not quiet_mode:
            raise
    return output


def log(log_str):
    print(log_str)


class NotFound(Exception):
    """
    Requested resource not found
    """
    error_code = 404


class BadRequest(Exception):
    """
    Incorrectly formatted  request
    """
    error_code = 400
