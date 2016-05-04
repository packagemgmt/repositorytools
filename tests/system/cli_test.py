import json
from unittest import TestCase
import logging
import os
import time
import requests

from repositorytools import cli

import config
GROUP = 'com.fooware'
ARTIFACT_LOCAL_PATH = 'test-1.0.txt'
METADATA = {"foo": "bar"}
CONTENT = 'foo'


class ArtifactCliTest(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

        with open(ARTIFACT_LOCAL_PATH, 'w') as f:
            f.write(CONTENT)

        self.artifact_cli = cli.ArtifactCLI()
        os.environ['REPOSITORY_USER'] = config.USER

    def tearDown(self):
        os.unlink(ARTIFACT_LOCAL_PATH)

    def test_upload_resolve_and_delete(self):
        # upload
        remote_artifacts = self.artifact_cli.run(['upload', ARTIFACT_LOCAL_PATH, config.REPO, GROUP])
        self.assertEquals(len(remote_artifacts), 1)
        remote_artifact = remote_artifacts[0]

        # resolve
        del os.environ['REPOSITORY_USER'] # to test that resolving works even without authentication
        urls = self.artifact_cli.run(['resolve', config.REPO, remote_artifact.get_coordinates_string()]).split('\n')

        self.assertEqual(1, len(urls))
        url = urls[0]
        r = requests.get(url, auth=(config.USER, os.environ['REPOSITORY_PASSWORD']))
        r.raise_for_status()
        self.assertEqual(r.text, CONTENT)

        # delete
        os.environ['REPOSITORY_USER'] = config.USER
        self.artifact_cli.run(['delete', remote_artifact.url])

    def test_metadata(self):
        remote_artifacts = cli.ArtifactCLI().run(['-D', 'upload', ARTIFACT_LOCAL_PATH, config.REPO, GROUP])
        self.assertEquals(len(remote_artifacts), 1)
        remote_artifact = remote_artifacts[0]

        self.artifact_cli.run(['set-metadata', '{s}'.format(s=json.dumps(METADATA)), remote_artifact.repo_id,
                               remote_artifact.get_coordinates_string()])
        metadata_received_serialized = self.artifact_cli.run(['get-metadata', remote_artifact.repo_id,
                                                             remote_artifact.get_coordinates_string()])
        metadata_received = json.loads(metadata_received_serialized)
        self.assertTrue(set(METADATA.items()).issubset(set(metadata_received.items())))
        self.artifact_cli.run(['delete', remote_artifact.url])


class RepoCliTest(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.repo_cli = cli.RepoCLI()
        self.artifact_cli = cli.ArtifactCLI()

        with open(ARTIFACT_LOCAL_PATH, 'w') as f:
            f.write('foo')

        self.artifact_cli = cli.ArtifactCLI()

    def tearDown(self):
        os.unlink(ARTIFACT_LOCAL_PATH)

    def test_create_list_and_drop(self):
        # create repo
        description = 'testing staging repo'
        repo_id = self.repo_cli.run(['create', '-s', '-d', description, config.REPO])

        # find the created repo in staging repos
        output_json = self.repo_cli.run(['list', '-s', '--output-format', 'json', '--filter',
                                         json.dumps({'repositoryId': repo_id})])
        output = json.loads(output_json)
        self.assertEqual(len(output), 1)
        output = json.loads(output_json)[0]
        self.assertEqual(output['repositoryId'], repo_id)
        self.assertEqual(output['description'], description)

        # drop the repo
        self.repo_cli.run(['drop', '-s', repo_id])

    def test_create_and_release(self):
        repo_id = self.repo_cli.run(['create', '-s', '-d', 'testing staging repo', config.REPO])
        self.repo_cli.run(['close', repo_id])
        time.sleep(1)
        self.repo_cli.run(['release', repo_id])

    def test_create_and_release_keep_metadata(self):
        remote_artifacts = self.artifact_cli.run(['upload', '--upload-filelist', '-s', ARTIFACT_LOCAL_PATH,
                                                  config.REPO, GROUP])
        remote_artifact = remote_artifacts[0]

        # without this sleep, it fails with 404: custom metadata indexing not supported for repository [test-xxxx]
        time.sleep(1)

        # added -D to increase coverage :)
        self.artifact_cli.run(['-D', 'set-metadata', json.dumps(METADATA), remote_artifact.repo_id,
                               remote_artifact.get_coordinates_string()])
        print self.repo_cli.run(['release', '--keep-metadata', remote_artifact.repo_id])
        metadata = self.artifact_cli.run(['get-metadata', config.REPO, remote_artifact.get_coordinates_string()])
        metadata = json.loads(metadata)
        self.assertTrue(set(METADATA.items()).issubset(set(metadata.items())))

    def test_list__staging_no_filter(self):
        self.repo_cli.run(['list', '-s'])