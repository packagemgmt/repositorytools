__all__ = ['NameVerDetectionError', 'Artifact', 'LocalArtifact', 'LocalRpmArtifact', 'RemoteArtifact']

import six.moves.urllib.parse
import itertools
import re
import os
import logging

logger = logging.getLogger(__name__)

class ArtifactError(Exception):
    pass


class NameVerDetectionError(ArtifactError):
    pass


class Artifact(object):
    """
    Generic class describing an artifact
    """
    def __init__(self, group, artifact='', version='', classifier='', extension=''):
        self.group = group
        self.artifact = artifact
        self.version = version
        self.classifier = classifier
        self.extension = extension

    def get_coordinates_string(self):
        return '{group}:{artifact}:{version}:{classifier}:{extension}'.format(group=self.group, artifact=self.artifact,
                                                                              version=self.version,
                                                                              classifier=self.classifier,
                                                                              extension=self.extension)

    def __repr__(self):
        return self.get_coordinates_string()


class LocalArtifact(Artifact):
    """
    Artifact for upload to repository
    """
    def __init__(self, group, local_path, artifact='', version='', classifier='', extension=''):
        self.local_path = local_path

        artifact_detected, version_detected, extension_detected = self.detect_name_ver_ext()

        if not artifact:
            artifact = artifact_detected

        if not version:
            version = version_detected

        if not extension:
            extension = extension_detected

        super(LocalArtifact, self).__init__(group=group, artifact=artifact, version=version, classifier=classifier,
                                            extension=extension)

    def detect_name_ver_ext(self):
        base_name = os.path.basename(self.local_path)
        result = re.match('^(?# name)(.*?)-(?=\d)(?# version)(\d.*)\.(?# extension)([^.]+)$', base_name)

        if result is None:
            raise NameVerDetectionError('Automatic detection of name and/or version failed for %s', self.local_path)

        name, version, extension = result.group(1), result.group(2), result.group(3)
        logger.debug('name: %s, version: %s, extension: %s', name, version, extension)
        return name, version, extension


class LocalRpmArtifact(LocalArtifact):
    """
    Special case of local artifact, which can detect it's coordinates from RPM metadata
    """
    @staticmethod
    def get_artifact_group(url):
        if url is None:
            raise Exception('Web pages of the package not present in RPM metadata, please fill the URL tag in specfile')

        parts = six.moves.urllib.parse.urlsplit(url).netloc.split(".")
        return ".".join(itertools.ifilter(lambda x: x != "www", reversed(parts)))

    def __init__(self, local_path, group=None):
        try:
            import rpm
        except ImportError:
            raise ArtifactError("Can't import rpm module to detect name and version")
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
    def __init__(self, group=None, artifact='', version='', classifier='', extension='', url=None, repo_id=None):
        super(RemoteArtifact, self).__init__(group=group, artifact=artifact, version=version, classifier=classifier,
                                             extension=extension)
        self.repo_id = repo_id
        self.url = url

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

        group, artifact, version = fields[0], fields[1], fields[2]

        classifier = extension = ''

        if len(fields) > 3:
            classifier = fields[3]

        if len(fields) > 4:
            extension = fields[4]

        return cls(group=group, artifact=artifact, version=version, classifier=classifier, extension=extension,
                   repo_id=repo_id)