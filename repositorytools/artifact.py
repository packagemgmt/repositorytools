__all__ = ['NameVerDetectionError', 'Artifact', 'LocalArtifact', 'LocalRpmArtifact', 'RemoteArtifact']

import rpm
import urlparse
import itertools
import re
import os


class ArtifactError(Exception):
    pass


class NameVerDetectionError(ArtifactError):
    pass


class Artifact(object):
    def __init__(self, group=None, artifact=None, version=None, classifier=None, extension=None):
        self.group = group
        self.artifact = artifact
        self.version = version
        self.classifier = classifier
        self.extension = extension


class LocalArtifact(Artifact):
    """
    Artifact for upload to repository
    """
    def __init__(self, group, local_path, artifact=None, version=None, classifier=None, extension=None):
        self.local_path = local_path

        if artifact is None and version is None:
            artifact, version = self.detect_name_and_version()

        super(LocalArtifact, self).__init__(group=group, artifact=artifact, version=version, classifier=classifier,
                                            extension=extension)

    def detect_name_and_version(self):
        base_name = os.path.basename(self.local_path)
        result = re.match('^(?# name)(.*?)-(?=\d)(?# version)(\d.*)(?# extension)(\.[^.]+)$', base_name)

        if result is None:
            raise NameVerDetectionError('Automatic detection of name and/or version failed for %s', self.local_path)

        return result.group(1), result.group(2)


class LocalRpmArtifact(LocalArtifact):
    @staticmethod
    def get_artifact_group(url):
        if url is None:
            raise Exception('Web pages of the package not present in RPM metadata, please fill the URL tag in specfile')

        parts = urlparse.urlsplit(url).netloc.split(".")
        return ".".join(itertools.ifilter(lambda x: x != "www", reversed(parts)))

    def __init__(self, local_path, group=None):
        ts = rpm.ts()
        fdno = os.open(local_path, os.O_RDONLY)
        headers = ts.hdrFromFdno(fdno)
        os.close(fdno)

        if not group:
            group = self.get_artifact_group(headers['url'])
        artifact = headers['name']
        version = '{v}-{r}'.format(v=headers['version'], r=headers['release'])
        super(LocalRpmArtifact, self).__init__(group=group, artifact=artifact, version=version, local_path=local_path)


class RemoteArtifact(Artifact):
    """
    Artifact in repository
    """
    def __init__(self, group=None, artifact=None, version=None, classifier=None, extension=None, url=None, repo_id=None):
        super(RemoteArtifact, self).__init__(group=group, artifact=artifact, version=version, classifier=classifier,
                                             extension=extension)
        self.url = url
        self.repo_id = repo_id

    def get_coordinates_string(self):
        return '{group}:{artifact}:{version}:{classifier}:{extension}'.format(group=self.group, artifact=self.artifact,
                                                                              version=self.version,
                                                                              classifier=self.classifier,
                                                                              extension=self.extension)

    @classmethod
    def from_repo_id_and_coordinates(cls, repo_id, coordinates):
        """

        :param repo_id:
        :param coordinates: e.g. 'com.fooware:foo:1.0.0'
        :return:
        """
        fields = coordinates.split(':')

        if len(fields) < 3:
            raise ArtifactError('Incorrect coordinates, at least group, artifact and version are obligatory')

        group, artifact, version = fields[0], fields [1], fields[2]

        classifier = extension = None

        if len(fields) > 3:
            classifier = fields[3]

        if len(fields) > 4:
            extension = fields[4]

        return cls(group=group, artifact=artifact, version=version, classifier=classifier, extension=extension,
                   repo_id=repo_id)