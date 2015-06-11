# Copyright 2015 Canonical Ltd.
# Licensed under the AGPLv3, see LICENCE file for details.
import logging
from logging.handlers import RotatingFileHandler
import os
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile

from mock import patch
from yaml import dump

from common_test_base import CommonTestBase
from utility import (
    ensure_dir,
    run_shell_command,
    setup_logging,
    StructuredMessage,
    temp_dir,
)


class TestUtility(CommonTestBase):

    def setUp(self):
        self.setup_test_logging()

    def test_ensure_dir(self):
        with temp_dir() as directory:
            expected_dir = os.path.join(directory, 'new_dir')
            ensure_dir(expected_dir)
            self.assertTrue(os.path.isdir(expected_dir))

    def test_ensure_dir_leaves_existing_files(self):
        with temp_dir() as directory:
            expected_file = os.path.join(directory, 'some_file')
            open(expected_file, 'a').close()
            ensure_dir(directory)
            self.assertTrue(os.path.isfile(expected_file))

    def test_ensure_dir_raises_when_existing(self):
        with self.assertRaises(BaseException):
            ensure_dir('/tmp/nofoo8765/new_dir')

    def test_run_shell_command(self):
        with patch('utility.check_output', autospec=True) as mock:
            run_shell_command('foo')
        mock.assert_called_once_with(['foo'])

    def test_run_shell_command_error(self):
        with self.assertRaisesRegexp(CalledProcessError, ""):
            run_shell_command('ls -W', quiet_mode=False)

    def test_run_shell_command_output(self):
        output = run_shell_command('echo "hello"')
        self.assertEqual(output, '"hello"\n')

    def test_setup_logging(self):
        with NamedTemporaryFile() as temp_file:
            setup_logging(temp_file.name, log_count=1, log_level=logging.DEBUG)
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertEqual(logger.name, 'root')
        handlers = logger.handlers
        self.assertIn(
            type(handlers[0]), [RotatingFileHandler, logging.StreamHandler])
        self.assertIn(
            type(handlers[1]), [RotatingFileHandler, logging.StreamHandler])

    def test_setup_logging_cmd_logger(self):
        with NamedTemporaryFile() as temp_file:
            setup_logging(temp_file.name, log_count=1, log_level=logging.INFO,
                          name='cmd_log', add_stream=False,
                          disable_formatter=True)
            logger = logging.getLogger('cmd_log')
            logger.info(StructuredMessage("deny-all", "3"))
            data = temp_file.read()
        self.assertEqual(logger.level, logging.INFO)
        self.assertEqual(logger.name, 'cmd_log')
        handlers = logger.handlers
        self.assertIn(type(handlers[0]), [RotatingFileHandler])
        expected_data = dump([['deny-all', "3"]])
        self.assertEqual(data, expected_data)

    def test_setup_logging_formatter(self):
        log_count = 1
        with NamedTemporaryFile() as temp_file:
            with patch('logging.Formatter') as l_mock:
                setup_logging(temp_file.name, log_count=log_count)
        logger = logging.getLogger()
        self.assertEqual(logger.name, 'root')
        l_mock.assert_called_once_with(
            '%(asctime)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S')

    def test_setup_logging_rotating_file_handler(self):
        log_count = 1
        with NamedTemporaryFile() as temp_file:
            with patch('utility.RotatingFileHandler') as mock:
                setup_logging(temp_file.name, log_count=log_count)
        mock.assert_called_once_with(
            temp_file.name, maxBytes=1024 * 1024 * 512, backupCount=log_count)

    def test_temp_dir(self):
        with temp_dir() as directory:
            self.assertTrue(os.path.isdir(directory))
        self.assertFalse(os.path.isdir(directory))

    def test_log(self):
        with NamedTemporaryFile() as temp_file:
            setup_logging(temp_file.name, log_count=1)
            logging.info('testing123')
            with open(temp_file.name, 'r') as file_reader:
                content = file_reader.read()
                # log format: 2015-04-29 14:03:02 INFO testing123
                match = content.split(' ', 2)[2]
                self.assertEqual(match, 'INFO testing123\n')

    def test_log_debug(self):
        with NamedTemporaryFile() as temp_file:
            setup_logging(temp_file.name, log_count=1, log_level=logging.DEBUG)
            logging.debug("testing123")
            with open(temp_file.name, 'r') as file_reader:
                content = file_reader.read()
                # log format: 2015-04-29 14:03:02 INFO testing123
                match = content.split(' ', 2)[2]
                self.assertEqual(match, 'DEBUG testing123\n')

    def test_log_error(self):
        with NamedTemporaryFile() as temp_file:
            setup_logging(temp_file.name, log_count=1)
            logging.error("testing123")
            with open(temp_file.name, 'r') as file_reader:
                content = file_reader.read()
                # log format: 2015-04-29 14:03:02 INFO testing123
                match = content.split(' ', 2)[2]
                self.assertEqual(match, 'ERROR testing123\n')
