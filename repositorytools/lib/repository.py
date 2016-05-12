"""
Contains classes for manipulating with a repository server
"""

__all__ = ['RepositoryClientError', 'WrongDataTypeError', 'ArtifactNotFoundError',
           'NexusRepositoryClient', 'NexusProRepositoryClient', 'repository_client_factory']

import requests
import logging
import os
import json
import base64

from repositorytools.lib.artifact import RemoteArtifact
from requests_toolbelt import MultipartEncoder

logger = logging.getLogger(__name__)


class RepositoryClientError(Exception):
    """
    Base exception raised when working with NexusRepositoryClient and its descendants
    """
    pass

class WrongDataTypeError(RepositoryClientError):
    pass

class ArtifactNotFoundError(RepositoryClientError):
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
    """
    Class for working with Sonatype Nexus OSS
    """
    DEFAULT_REPOSITORY_URL = 'https://repository'

    def __init__(self, repository_url=None, user=None, password=None, verify_ssl=True):
        """

        :param repository_url: url to repository server
        :param user: username for connecting to repository
        :param password: password for connecting to repository
        :param verify_ssl: False if you don't want to verify SSL certificate of the server
        :return:
        """
        self._verify_ssl = verify_ssl

        if repository_url:
            self._repository_url = repository_url
        else:
            self._repository_url = os.environ.get('REPOSITORY_URL', self.DEFAULT_REPOSITORY_URL)

        self._session = requests.session()

        if not user:
            user = os.environ.get('REPOSITORY_USER')

        if user:
            if not password:
                try:
                    password = os.environ['REPOSITORY_PASSWORD']
                except KeyError:
                    logger.error('Repository password not specified. Please specify repository password in environment'
                                 ' variable "REPOSITORY_PASSWORD"')
            self._session.auth = (user, password)

    def resolve_artifact(self, remote_artifact):
        data = self._send_json('service/local/artifact/maven/resolve', params=dict(g=remote_artifact.group,
                                                               a=remote_artifact.artifact,
                                                               v=remote_artifact.version,
                                                               r=remote_artifact.repo_id,
                                                               c=remote_artifact.classifier,
                                                               e=remote_artifact.extension))['data']

        remote_artifact.url = '{repository_url}/content/repositories/{repo}/{artifact_path}'.format(
            repository_url=self._repository_url, repo=remote_artifact.repo_id, artifact_path=data['repositoryPath'])

    def upload_artifacts(self, local_artifacts, repo_id, print_created_artifacts=True, _hostname_for_download=None,
                         _path_prefix='content/repositories', use_direct_put=False):
        """
        Uploads artifacts to repository.

        :param local_artifacts: list[LocalArtifact]
        :param repo_id: id of target repository
        :param print_created_artifacts: if True prints to stdout what was uploaded and where
        :return: list[RemoteArtifact]
        """

        # upload files
        remote_artifacts = []

        for local_artifact in local_artifacts:
            remote_artifact = self._upload_artifact(local_artifact=local_artifact, path_prefix=_path_prefix,
                                                    repo_id=repo_id, hostname_for_download=_hostname_for_download,
                                                    use_direct_put=use_direct_put)
            remote_artifacts.append(remote_artifact)

        if print_created_artifacts:
            NexusRepositoryClient._print_created_artifacts(remote_artifacts, repo_id)

        return remote_artifacts

    def _upload_artifact(self, local_artifact, path_prefix, repo_id, hostname_for_download=None, use_direct_put=False):

        filename = os.path.basename(local_artifact.local_path)
        logger.info('-> Uploading %s', filename)
        logger.debug('local artifact: %s', local_artifact)

        # rgavf stands for repo-group-local_artifact-version-filename
        gavf = '{group}/{name}/{ver}/{filename}'.format(group=local_artifact.group.replace('.', '/'),
                                                        name=local_artifact.artifact, ver=local_artifact.version,
                                                        filename=filename)
        rgavf = '{repo_id}/{gavf}'.format(repo_id=repo_id, gavf=gavf)

        with open(local_artifact.local_path, 'rb') as f:
            if not use_direct_put:
                data = {
                    'g':local_artifact.group,
                    'a':local_artifact.artifact,
                    'v':local_artifact.version,
                    'r':repo_id,
                    'e': local_artifact.extension,
                    'p': local_artifact.extension,
                    'hasPom': 'false'
                }


                data_list = data.items()
                data_list.append( ('file', (filename, f, 'text/plain') ))
                m_for_logging = MultipartEncoder(fields=data_list)
                logger.debug('payload: %s', m_for_logging.to_string())

                f.seek(0)
                m = MultipartEncoder(fields=data_list)
                headers = {'Content-Type': m.content_type}

                self._send('service/local/artifact/maven/content', method='POST', data=m, headers=headers)

                result = RemoteArtifact(group=local_artifact.group, artifact=local_artifact.artifact,
                                      version=local_artifact.version, classifier=local_artifact.classifier,
                                      extension=local_artifact.extension, repo_id=repo_id)
                self.resolve_artifact(result)
                return result

            else:
                headers = {'Content-Type': 'application/x-rpm'}
                remote_path = '{path_prefix}/{rgavf}'.format(path_prefix=path_prefix, rgavf=rgavf)
                self._send(remote_path, method='PUT', headers=headers, data=f)

                # if not specified, use repository url
                hostname_for_download = hostname_for_download or self._repository_url
                url = '{hostname}/content/repositories/{rgavf}'.format(hostname=hostname_for_download, rgavf=rgavf)

                # get classifier and extension from nexus
                path = 'service/local/repositories/{repo_id}/content/{gavf}?describe=maven2'.format(repo_id=repo_id, gavf=gavf)
                maven_metadata = self._send_json(path)['data']

                return RemoteArtifact(group=maven_metadata['groupId'], artifact=maven_metadata['artifactId'],
                                      version=maven_metadata['version'], classifier=maven_metadata.get('classifier', ''),
                                      extension=maven_metadata.get('extension', ''), url=url, repo_id=repo_id)

    def delete_artifact(self, url):
        """
        Deletes an artifact from repository.

        :param url: string
        :return:
        """
        r = self._session.delete(url)
        r.raise_for_status()

    @staticmethod
    def _print_created_artifacts(remote_artifacts, repo_id):
        caption = 'The following files were uploaded to repository {repo_id}'.format(repo_id=repo_id)

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

    def _send_json(self, path, json_data=None, method='GET', params=None):
        headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
        if json_data is None:
            data = None
        else:
            data = json.dumps(json_data)
        r = self._send(path, data=data, headers=headers, method=method, params=params)

        if r.text:
            return json.loads(r.text)

    @staticmethod
    def _first_contains_second(first, second):
        """
        :param first dict
        :param second dict
        :return True if first has all keys from second and that they have same value
        """

        # to protect a user from hard-to-debug problems with incorrect data type
        # once I sent here a string with serialized dict and it took me hours to find the bug!
        if not isinstance(first, dict) or not isinstance(second, dict):
            raise WrongDataTypeError('Both arguments should be dict')

        result = all(k in first and first[k] == second[k] for k in second)
        return result


class NexusProRepositoryClient(NexusRepositoryClient):
    """
    Class for working with Sonatype Nexus Professional
    """
    def __init__(self, repository_url=None, user=None, password=None, verify_ssl=True, staging_repository_url=None):
        super(NexusProRepositoryClient, self).__init__(repository_url=repository_url, user=user, password=password,
                                                       verify_ssl=verify_ssl)

        """
        We redirect users to mirrors, but we don't mirror staging repositories, we when we upload artifacts and populate
        remote_url, we have to put there different alias of the repository server, which causes that they will not be
        redirected.
        """
        if staging_repository_url:
            self._staging_repository_url = staging_repository_url
        else:
            self._staging_repository_url = os.environ.get('STAGING_REPOSITORY_URL', self._repository_url)

    def upload_artifacts_to_staging(self, local_artifacts, repo_id, print_created_artifacts=True, upload_filelist=False):
        """
        :param local_artifacts: list[LocalArtifact]
        :param repo_id: name of staging repository
        :param print_created_artifacts: if True prints to stdout what was uploaded and where
        :param staging: bool
        :param upload_filelist: if True, creates and uploads a list of uploaded files

        :return: list[RemoteArtifact]
        """
        hostname_for_download = self._staging_repository_url
        path_prefix = 'service/local/staging/deployByRepositoryId'

        # upload files
        remote_artifacts = self.upload_artifacts(local_artifacts, repo_id, print_created_artifacts,
                                                 hostname_for_download, path_prefix, use_direct_put=True)

        # upload filelist
        if upload_filelist:
            coord_list = [a.get_coordinates_string() for a in remote_artifacts]
            data = '\n'.join(coord_list)
            remote_path = '{path_prefix}/{repo_id}/{filelist_path}'.format(path_prefix=path_prefix, repo_id=repo_id,
                                                                           filelist_path=self._get_filelist_path(repo_id))
            self._send(remote_path, method='POST', data=data, headers={'Content-Type': 'text/csv'})

        return remote_artifacts

    def upload_artifacts_to_new_staging(self, local_artifacts, repo_id, print_created_artifacts=True,
                                        description='No description', upload_filelist=False):
        """
        Creates a staging repository in staging profile with name repo_id and uploads local_artifacts there.

        :param local_artifacts: list[LocalArtifact]
        :param repo_id: name of target repository
        :param print_created_artifacts: if True prints to stdout what was uploaded and where
        :param description: description of staging repo
        :param upload_filelist: see upload_artifacts_to_staging

        :return: list[RemoteArtifact]
        """
        repo_id = self.create_staging_repo(repo_id, description)
        remote_artifacts = self.upload_artifacts_to_staging(local_artifacts, repo_id, print_created_artifacts, upload_filelist)

        # close staging repo
        self.close_staging_repo(repo_id)
        return remote_artifacts

    @staticmethod
    def _get_filelist_path(repo_id):
        return '{repo_id}-filelist'.format(repo_id=repo_id)

    def get_artifact_metadata(self, remote_artifact):
        """
        Gets artifact's maven metadata.

        Metadata capability needs to be enabled to use this. Also indexing has to be enabled for that repo to make it
        work.

        :param remote_artifact:
        :return:
        """
        artifact_id = 'urn:maven/artifact#{coordinates}'.format(coordinates=remote_artifact.get_coordinates_string())
        logger.debug('artifact_id: %s', artifact_id)
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
        Sets artifact metadata.

        The same requirements as for get_artifact_metadata have to be met.

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
        logger.debug('artifact_id: %s', artifact_id)
        artifact_id_encoded = base64.b64encode(artifact_id)

        metadata_raw = []

        for key, value in metadata.iteritems():
            metadata_raw.append({"key": key, "value": value})

        return self._send_json('service/local/index/custom_metadata/{repo_id}/{artifact_id_encoded}'.format(
                               repo_id=remote_artifact.repo_id, artifact_id_encoded=artifact_id_encoded), method='POST',
                               json_data={"data": metadata_raw})

    def list_staging_repos(self, filter_dict=None):
        """

        :param filter_dict: dictionary with filters, for example {'description':'foo'}
        :return: list of dictionaries, each dict describes one staging repo
        """
        r = self._send_json('service/local/staging/profile_repositories')
        data = r['data']

        if not filter_dict:
            result = data
        else:
            result = [d for d in data if self._first_contains_second(d, filter_dict)]

        logger.debug('list_staging_repos result: %s', result)
        return result

    def create_staging_repo(self, profile_name, description):
        """
        Creates a staging repository
        :param profile_name: name of staging profile
        :param description: description of created staging repository
        :return: id of newly created staging repository
        """
        profile = self._get_staging_profile(profile_name)
        logger.info('Creating staged repo in profile %s, description: %s', profile_name, description)
        r = self._send_json('service/local/staging/profiles/{id}/start'.format(id=profile['id']),
                            {'data': {'description': description}}, method='POST')
        result = r['data']['stagedRepositoryId']
        logger.info('Created staged repo with ID %s', result)
        return result

    def close_staging_repo(self, repo_id, description=''):
        """
        Closes a staging repository. After close, no files can be added.

        :param repo_id: id of staging repository
        :param description: if specified, updates description of staged repository
        :return:
        """
        self.close_staging_repos([repo_id], description)

    def close_staging_repos(self, repo_ids, description=''):
        """
        Closes multiple staging repositories.

        :param repo_ids: list of repo IDs (strings)
            For description of other params see close_staging_repo.
        :param description: Description message.
        :return:
        """
        data = {'data': {'stagedRepositoryIds': repo_ids, 'description': description}}
        return self._send_json('service/local/staging/bulk/close', data, method='POST')

    def drop_staging_repo(self, repo_id, description='No description'):
        """
        Deletes a staging repository and all artifacts inside.

        :param repo_id: id of staging repository
        :return:
        """
        self.drop_staging_repos([repo_id], description=description)

    def drop_staging_repos(self, repo_ids, description='No description'):
        """
        Deletes multiple staging repositories.

        :param repo_ids: list of repo IDs (strings)
        :return:
        """
        data = {'data': {'stagedRepositoryIds': repo_ids, 'description': description}}
        return self._send_json('service/local/staging/bulk/drop', data, method='POST')

    def release_staging_repo(self, repo_id, description='No description', auto_drop_after_release=True,
                             keep_metadata=False):
        """
        Releases all contents of a staging repository to a release repository which this staging repository targets.

        :param repo_id: id of staging repository
        :param description:
        :param auto_drop_after_release: set this to True if you want to delete the staging repository after releasing
        :param keep_metadata: Keeps custom maven metadata of artifacts after release. Works only there is list of
         artifacts created by upload_artifacts_to_new_staging with upload_filelist=False. It is because current Nexus 2.x
         can't do keep the metadata after release, so we manually read the metadata, release and then set them again.
        :return:
        """
        if keep_metadata:
            # download list of artifacts
            resp = self._send('content/repositories/{repo_id}/{filelist_path}'.format(repo_id=repo_id,
                                                                                      filelist_path=self._get_filelist_path(repo_id)))

            artifacts = [RemoteArtifact.from_repo_id_and_coordinates(repo_id, coordinates=coords)
                        for coords in resp.text.split('\n')]

            # download metadata for all files
            for artifact in artifacts:
                artifact.metadata = self.get_artifact_metadata(artifact)

            release_repo_id = self._get_target_repository(repo_id)

        data = {'data': {'stagedRepositoryIds': [repo_id], 'description': description,
                         'autoDropAfterRelease': auto_drop_after_release}}
        result = self._send_json('service/local/staging/bulk/promote', data, method='POST')

        if keep_metadata:
            for artifact in artifacts:
                artifact.repo_id = release_repo_id
                self.set_artifact_metadata(artifact, artifact.metadata)

        return result

    def _get_staging_profile(self, name):
        staging_profiles = self._send_json('service/local/staging/profiles')

        for i in staging_profiles["data"]:
            if i["name"] == name:
                return i

        raise RepositoryClientError('No staging profile with name {name}'.format(name=name))

    def _get_target_repository(self, staging_repo_id):
        data = self._send_json('service/local/staging/repository/{staging_repo_id}'.format(staging_repo_id=staging_repo_id))
        return data['releaseRepositoryId']
