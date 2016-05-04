from unittest import TestCase
import logging
import six

from repositorytools import LocalArtifact


class ArtifactTest(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def test_detect_name_ver_ext(self):
        artifacts = {
            'my_local_path/devbox-2.0.0.tgz': ('devbox', '2.0.0', 'tgz'),
            'my_local_path/python-foo2-2.3.4.ext': ('python-foo2', '2.3.4', 'ext'),
            'my_local_path/infra-6.6-4.tgz': ('infra', '6.6-4', 'tgz'),
            'my_local_path/update-hostname-0.1.4-1.el6.noarch.rpm': ('update-hostname', '0.1.4-1.el6.noarch', 'rpm'),
            'my_local_path/test-1.0.txt': ('test', '1.0', 'txt')
        }

        for local_path, nameverext in six.iteritems(artifacts):
            expected_name, expected_version, expected_extension = nameverext
            local_artifact = LocalArtifact('com.fooware', local_path=local_path)

            self.assertEqual(expected_name, local_artifact.artifact)
            self.assertEqual(expected_version, local_artifact.version)
            self.assertEqual(expected_extension, local_artifact.extension)
