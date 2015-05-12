"""
Contains classes for manipulating with a repository server
"""

__all__ = ['RepositoryClientError', 'NexusRepositoryClient', 'NexusProRepositoryClient', 'repository_client_factory']

import requests
import logging
import os
import json
import base64

from artifact import RemoteArtifact

logger = logging.getLogger(__name__)


class RepositoryClientError(Exception):
    pass


def repository_client_factory(*args, **kwargs):
    """
    Detects which kind of repository user wants to use and returns appropriate instance of it.
    :param args:
    :param kwargs:
    :return:
    """
    # short-term TODO: detect between Nexus and NexusPro
    # long-term TODO: detect and support also Artifactory and ArtifactoryPro
    return NexusProRepositoryClient(*args, **kwargs)


class NexusRepositoryClient(object):
    DEFAULT_REPOSITORY_URL = 'https://repository'

    def __init__(self, repository_url=None, user='admin', password=None, staging_repository_url=None, verify_ssl=True):
        self._verify_ssl = verify_ssl
        if not password:
            try:
                password = os.environ['REPOSITORY_PASSWORD']
            except KeyError:
                logger.error('Repository password not specified. Please specify repository password in environment'
                             ' variable "REPOSITORY_PASSWORD"')

        if repository_url:
            self._repository_url = repository_url
        else:
            self._repository_url = os.environ.get('REPOSITORY_URL', self.DEFAULT_REPOSITORY_URL)

        self._session = requests.session()
        self._session.auth = (user, password)

        """
        We redirect users to mirrors, but we don't mirror staging repositories, we when we upload artifacts and populate
        remote_url, we have to put there different alias of the repository server, which causes that they will not be
        redirected.
        """
        if staging_repository_url:
            self._staging_repository_url = staging_repository_url
        else:
            self._staging_repository_url = os.environ.get('STAGING_REPOSITORY_URL', self._repository_url)

    def upload_artifacts(self, local_artifacts, repo, staging, description='No description', upload_filelist=False,
                         print_created_artifacts=True):
        """

        :param local_artifacts: list[LocalArtifact]
        :param repo: name of target repository
        :param staging: bool
        :param description: description of staging repo
        :param upload_filelist: for staging repos, creates and uploads a list of uploaded files
        :param print_created_artifacts: if True prints to stdout what was uploaded and where
        :return: list[RemoteArtifact]
        """
        repo_id = repo

        if staging:
            repo_id = self.create_staging_repo(repo, description)
            logger.info('> Created staged repo with ID %s', repo_id)
            hostname_for_download = self._staging_repository_url
            path_prefix = 'service/local/staging/deployByRepositoryId'
        else:
            hostname_for_download = self._repository_url
            path_prefix = 'content/repositories'

        # upload files
        remote_artifacts = []

        for local_artifact in local_artifacts:
            remote_artifact = self._upload_artifact(local_artifact, path_prefix, repo_id, hostname_for_download)
            remote_artifacts.append(remote_artifact)

            # upload filelist
            if staging and upload_filelist:
                coord_list = [a.get_coordinates_string() for a in remote_artifacts]
                data = '\n'.join(coord_list)
                remote_path = '{path_prefix}/{repo_id}/{repo_id}-filelist'.format(path_prefix=path_prefix,
                                                                                  repo_id=repo_id)
                self._send(remote_path, method='POST', data=data, headers={'Content-Type': 'text/csv'})

        if print_created_artifacts:
            NexusRepositoryClient._print_created_artifacts(remote_artifacts, repo_id)

        # close staging repo
        if staging:
            self.close_staging_repo(repo_id)

        return remote_artifacts

    def _upload_artifact(self, local_artifact, path_prefix, repo_id, hostname_for_download=None):

        filename = os.path.basename(local_artifact.local_path)
        logger.info('-> Uploading %s', filename)

        with open(local_artifact.local_path, 'rb') as f:
            headers = {'Content-Type': 'application/x-rpm'}

            """rgavf stands for repo-group-local_artifact-version-filename"""
            rgavf = '{repo_id}/{group}/{name}/{ver}/{filename}'.format(
                repo_id=repo_id, group=local_artifact.group.replace('.', '/'),
                name=local_artifact.artifact, ver=local_artifact.version, filename=filename)

            remote_path = '{path_prefix}/{rgavf}'.format(path_prefix=path_prefix, rgavf=rgavf)
            self._send(remote_path, method='POST', headers=headers, data=f)

        # if not specified, use repository url
        hostname_for_download = hostname_for_download or self._repository_url
        url = '{hostname}/content/repositories/{rgavf}'.format(hostname=hostname_for_download, rgavf=rgavf)

        return RemoteArtifact(group=local_artifact.group, artifact=local_artifact.artifact,
                              version=local_artifact.version, classifier=local_artifact.classifier,
                              extension=local_artifact.extension, url=url, repo_id=repo_id)

    def delete_artifact(self, url):
        """

        :param url: string
        :return:
        """
        r = self._session.delete(url)
        r.raise_for_status()

    @staticmethod
    def _print_created_artifacts(remote_artifacts, repo_id):
        caption = 'The following files where uploaded to repository {repo_id}'.format(repo_id=repo_id)

        if os.environ.get('TEAM_CITY_URL'):
            for remote_artifact in remote_artifacts:
                text = '<a href="{url}">{url}</a>'.format(url=remote_artifact.url)
                print("##teamcity[highlight title='{caption}' text='{text}']".format(caption=caption, text=text))

        else:
            print(caption)

            for remote_artifact in remote_artifacts:
                print(remote_artifact.url)

    def _send(self, path, method='GET', **kwargs):
        r = self._session.request(method, '{hostname}/{path}'.format(hostname=self._repository_url, path=path),
                                  verify=self._verify_ssl,
                                  **kwargs)

        logger.debug('response: %s', r.text)
        r.raise_for_status()

        return r

    def _send_json(self, path, json_data=None, method='GET'):
        headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
        if json_data is None:
            data = None
        else:
            data = json.dumps(json_data)
        r = self._send(path, data=data, headers=headers, method=method)

        if r.text:
            return json.loads(r.text)


class NexusProRepositoryClient(NexusRepositoryClient):
    def get_artifact_metadata(self, remote_artifact):
        """
        Gets artifact metadata, metadata capability needs to be enabled to use this. Also indexing has to be enabled
        for that repo to make it work.

        :param remote_artifact:
        :return:
        """
        artifact_id = 'urn:maven/artifact#{coordinates}'.format(coordinates=remote_artifact.get_coordinates_string())
        artifact_id_encoded = base64.b64encode(artifact_id)
        metadata_raw = self._send_json('service/local/index/custom_metadata/{repo_id}/{artifact_id_encoded}'.format(
            repo_id=remote_artifact.repo_id, artifact_id_encoded=artifact_id_encoded))

        metadata = {}

        for d in metadata_raw['data']:
            try:
                metadata[d["key"]] = d["value"]
            except KeyError:
                raise RepositoryClientError('Malformed artifact metadata. Missing key or value at artifact {atrifact}'.format(
                    artifact=remote_artifact
                ))

        return metadata

    def set_artifact_metadata(self, remote_artifact, metadata):
        """
        Sets artifact metadata

        :param remote_artifact:
        :param metadata: dict of keys and values you want to save there
        :return:
        """
        """
        check args
        """
        if not isinstance(metadata, dict):
            raise RepositoryClientError('Metadata has to be a dictionary')

        artifact_id = 'urn:maven/artifact#{coordinates}'.format(coordinates=remote_artifact.get_coordinates_string())
        artifact_id_encoded = base64.b64encode(artifact_id)

        metadata_raw = []

        for key, value in metadata.iteritems():
            metadata_raw.append({"key": key, "value": value})

        return self._send_json('service/local/index/custom_metadata/{repo_id}/{artifact_id_encoded}'.format(
                               repo_id=remote_artifact.repo_id, artifact_id_encoded=artifact_id_encoded), method='POST',
                               json_data={"data": metadata_raw})

    def create_staging_repo(self, profile_name, description):
        profile = self._get_staging_profile(profile_name)
        logger.info('> Creating staged repo in profile %s', profile_name)
        r = self._send_json('service/local/staging/profiles/{id}/start'.format(id=profile['id']),
                            {'data': {'description': description}}, method='POST')
        return r['data']['stagedRepositoryId']

    def close_staging_repo(self, repo_id, description='No description'):
        data = {'data': {'stagedRepositoryIds': [repo_id], 'description': description}}
        return self._send_json('service/local/staging/bulk/close', data, method='POST')

    def drop_staging_repo(self, repo_id, description='No description'):
        data = {'data': {'stagedRepositoryIds': [repo_id], 'description': description}}
        return self._send_json('service/local/staging/bulk/drop', data, method='POST')

    def release_staging_repo(self, repo_id, description='No description', auto_drop_after_release=True):
        data = {'data': {'stagedRepositoryIds': [repo_id], 'description': description,
                         'autoDropAfterRelease': auto_drop_after_release}}
        return self._send_json('service/local/staging/bulk/promote', data, method='POST')

    def _get_staging_profile(self, name):
        staging_profiles = self._send_json('service/local/staging/profiles')

        for i in staging_profiles["data"]:
            if i["name"] == name:
                return i

        raise RepositoryClientError('No staging profile with name {name}'.format(name=name))