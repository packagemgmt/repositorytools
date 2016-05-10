# -*- coding: utf-8 -*-
import argparse
import unittest

from repositorytools.cli.common import CLI


class MyCli(CLI):
    def _get_parser(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('hello', help='Say hello')
        subparser.set_defaults(func=self.hello)
        return parser

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def hello(self, args):
        return "hello"


my_cli = MyCli()


class TestCLI(unittest.TestCase):
    def test_call(self):
        """ __call__() must return 0 (success) """
        result = my_cli(["hello"])
        self.assertEqual(result, 0)
