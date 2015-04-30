from __future__ import print_function

import logging
from logging.handlers import RotatingFileHandler

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
        logging.error("Command generated error: %s " % cmd)
        if not quiet_mode:
            raise
    return output


def setup_logging(log_path, log_count):
    """Install log handlers to output to file and stream."""
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                                  '%Y-%m-%d %H:%M:%S')
    root_logger = logging.getLogger()
    rf_handler = RotatingFileHandler(
        log_path, maxBytes=1024 * 1024 * 512, backupCount=log_count)
    rf_handler.setFormatter(formatter)
    root_logger.addHandler(rf_handler)
    s_handler = logging.StreamHandler()
    s_handler.setFormatter(formatter)
    root_logger.addHandler(s_handler)
    root_logger.setLevel(logging.DEBUG)


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
