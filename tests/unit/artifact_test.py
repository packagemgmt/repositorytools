from unittest import TestCase
import logging

from repositorytools.artifact import *


class ArtifactTest(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def test_detect_name_and_version(self):
        artifacts = {
            'my_local_path/devbox-2.0.0.tgz': ('devbox', '2.0.0'),
            'my_local_path/python-foo2-2.3.4.ext': ('python-foo2', '2.3.4'),
            'my_local_path/infra-6.6-4.tgz': ('infra', '6.6-4'),
            'my_local_path/update-hostname-0.1.4-1.el6.noarch.rpm': ('update-hostname', '0.1.4-1.el6.noarch')
        }

        for local_path, namever in artifacts.iteritems():
            expected_name, expected_version = namever
            local_artifact = LocalArtifact('com.fooware', local_path=local_path)

            self.assertEqual(expected_name, local_artifact.artifact)
            self.assertEqual(expected_version, local_artifact.version)