# Copyright 2015 Canonical Ltd.
# Licensed under the AGPLv3, see LICENCE file for details.
import logging

from unittest import TestCase

from chaos_monkey import ChaosMonkey

__metaclass__ = type


class CommonTestBase(TestCase):

    def verify_equals_to_all_chaos(self, chaos):
        all_chaos, _ = ChaosMonkey.get_all_chaos()
        self.assertEqual(
            sorted(all_chaos, key=lambda k: k.command_str),
            sorted(chaos, key=lambda k: k.command_str))

    def get_command_str(self, chaos):
        return [c.command_str for c in chaos]

    def setup_test_logging(self):
        logger = logging.getLogger()
        orig_handlers = logger.handlers
        logger.handlers = []
        orig_level = logger.level
        self.addCleanup(self.restore_test_logging, orig_handlers, orig_level)

    def restore_test_logging(self, orig_handler, orig_level):
        logger = logging.getLogger()
        logger.handlers = orig_handler
        logger.level = orig_level
