import json
from unittest import TestCase
import logging
import os
import time

from repositorytools import cli

REPO = 'test'
GROUP = 'com.fooware'


class ArtifactCliTest(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.artifact_local_path = 'test-1.0.txt'

        with open(self.artifact_local_path, 'w') as f:
            f.write('foo')

        self.artifact_cli = cli.ArtifactCLI()

    def tearDown(self):
        os.unlink(self.artifact_local_path)

    def test_upload_and_delete(self):
        remote_artifacts = self.artifact_cli.run(['upload', self.artifact_local_path, REPO, GROUP])
        self.assertEquals(len(remote_artifacts), 1)
        remote_artifact = remote_artifacts[0]
        self.artifact_cli.run(['delete', remote_artifact.url])

    def test_metadata(self):
        """
        Requires nexus professional
        :return:
        """
        remote_artifacts = cli.ArtifactCLI().run(['upload', self.artifact_local_path, REPO, GROUP])
        self.assertEquals(len(remote_artifacts), 1)
        remote_artifact = remote_artifacts[0]

        metadata = {"foo": "bar"}

        self.artifact_cli.run(['set-metadata', remote_artifact.repo_id, remote_artifact.get_coordinates_string(),
                              '{s}'.format(s=json.dumps(metadata))])
        metadata_received_serialized = self.artifact_cli.run(['get-metadata', remote_artifact.repo_id,
                                                             remote_artifact.get_coordinates_string()])
        metadata_received = json.loads(metadata_received_serialized)
        self.assertTrue(set(metadata.items()).issubset(set(metadata_received.items())))
        self.artifact_cli.run(['delete', remote_artifact.url])


class RepoCliTest(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.repo_cli = cli.RepoCLI()

    def test_create_and_drop(self):
        repo_id = self.repo_cli.run(['create', '-s', '-d', 'testing staging repo', REPO])
        self.repo_cli.run(['drop', '-s', repo_id])

    def test_create_and_release(self):
        repo_id = self.repo_cli.run(['create', '-s', '-d', 'testing staging repo', REPO])
        self.repo_cli.run(['close', repo_id])
        time.sleep(1)
        self.repo_cli.run(['release', repo_id])