from unittest import TestCase
import logging

from repositorytools import NexusRepositoryClient, WrongDataTypeError


class NexusRepositoryTest(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def test_first_contains_second(self):
        first = {u'repositoryId': u'test-1345', u'profileType': u'repository'}
        second = {"repositoryId": "test-1345"}

        self.assertTrue(NexusRepositoryClient._first_contains_second(first, second))
        self.assertFalse(NexusRepositoryClient._first_contains_second(second, first))
        self.assertFalse(NexusRepositoryClient._first_contains_second(dict(x=1), dict(y=1)))
        self.assertRaises(WrongDataTypeError, NexusRepositoryClient._first_contains_second, 123, 'abc')