"""
Command line interface
"""

from abc import ABCMeta, abstractmethod
import argparse
import json
import logging
import httplib as http_client
import sys

import repositorytools

logger = logging.getLogger(sys.argv[0])


def configure_logging(debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        http_client.HTTPConnection.debuglevel = 1
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.INFO)
        requests_log.propagate = True
    else:
        logging.basicConfig(level=logging.INFO)


class CLI(object):
    __metaclass__ = ABCMeta

    """
    Base class for cli
    """
    @abstractmethod
    def _get_parser(self):
        """
        :return: argparse.ArgumentParser
        """
        pass

    def __init__(self):
        self.parser = self._get_parser()
        self.parser.add_argument("-D", "--debug", action="store_true", dest="debug", default=False,
                                 help="Print lots of debugging information")
        self.repository = repositorytools.repository_client_factory()

    def run(self, args=None):
        args_namespace = self.parser.parse_args(args)
        configure_logging(args_namespace.debug)
        logger.info('Started %s', str(sys.argv))

        """
        This runs the function that is assigned to the sub-command by calling of set_defaults
        """
        return args_namespace.func(args_namespace)


class ArtifactCLI(CLI):
    def _get_parser(self):
        parser = argparse.ArgumentParser(description='A command line tool for working with artifacts')
        subparsers = parser.add_subparsers()

        # upload
        parser_upload = subparsers.add_parser('upload', help='Uploads an artifact to repository, can detect name and'
                                                             ' version from filename')
        parser_upload.add_argument("-s", "--staging", action="store_true", dest="staging", default=False,
                            help="Uploads to a newly created staging repository which targets given repository")
        parser_upload.add_argument("--upload-filelist", action="store_true", default=False, help="uploads list of uploaded "
                                                                                                 "files")
        parser_upload.add_argument("--artifact", help="name of artifact, if omitted, will be detected from filename")
        parser_upload.add_argument("--version", help="version of artifact, if omitted, will be detected from filename")
        parser_upload.add_argument("-d", "--description", dest="description", default='No description',
                                   help="Description of a staging repository")

        parser_upload.add_argument("local_file", help="path to an artifact on your machine")
        parser_upload.add_argument("repo_id", help="id of target repository")
        parser_upload.add_argument("group", help="artifact group")
        parser_upload.set_defaults(func=self.upload)

        # delete
        parser_delete = subparsers.add_parser('delete', help='Deletes an artifact from repository')
        parser_delete.add_argument("url", help="URL of the artifact")
        parser_delete.set_defaults(func=self.delete)

        # get metadata
        parser_get_metadata = subparsers.add_parser('get-metadata', help="Prints artifact's metadata")
        parser_get_metadata.add_argument("repo_id", help="id of repository containing the artifact")
        parser_get_metadata.add_argument("coordinates", help="group:artifact:version[:classifier[:extension]]")
        parser_get_metadata.set_defaults(func=self.get_metadata)

        # set metadata
        parser_get_metadata = subparsers.add_parser('set-metadata', help="Sets artifact's metadata")
        parser_get_metadata.add_argument("repo_id", help="id of repository containing the artifact")
        parser_get_metadata.add_argument("coordinates", help="group:artifact:version[:classifier[:extension]]")
        parser_get_metadata.add_argument("metadata", help="Dict in JSON format. All keys and values have to be strings,"
                                                          "e.g. '{\"key1\":\"value1\",\"key2\":\"value2\"}'")
        parser_get_metadata.set_defaults(func=self.set_metadata)
        return parser

    def upload(self, args):
        try:
            artifact = repositorytools.LocalArtifact(local_path=args.local_file, group=args.group,
                                                     artifact=args.artifact, version=args.version)
        except repositorytools.NameVerDetectionError:
            logger.exception('Unable to create instance of artifact.')
            sys.exit(1)

        if args.staging:
            return self.repository.upload_artifacts_to_new_staging([artifact], args.repo_id, True,
                                                                   description=args.description,
                                                                   upload_filelist=args.upload_filelist)
        else:
            return self.repository.upload_artifacts([artifact], args.repo_id, True)

    def delete(self, args):
        self.repository.delete_artifact(args.url)

    def get_metadata(self, args):
        artifact = repositorytools.RemoteArtifact.from_repo_id_and_coordinates(args.repo_id, args.coordinates)
        metadata = self.repository.get_artifact_metadata(artifact)
        output = json.dumps(metadata)
        print(output)
        return output

    def set_metadata(self, args):
        artifact = repositorytools.RemoteArtifact.from_repo_id_and_coordinates(args.repo_id, args.coordinates)
        metadata = json.loads(args.metadata)
        self.repository.set_artifact_metadata(artifact, metadata)


class RepoCLI(CLI):
    def _get_parser(self):
        parser = argparse.ArgumentParser(description='A command line tool for working with repositories')
        subparsers = parser.add_subparsers()

        # create
        parser_create = subparsers.add_parser('create', help='Creates a repository')
        parser_create.add_argument("-s", "--staging", action="store_true", help='Creates a staging repository with'
                                                                                ' target to given repo')
        parser_create.add_argument("-d", "--description", help='description of staged repo', default='no description')
        parser_create.add_argument("repo_id", help='id of the repository, if used with -s, it is id of'
                                                   'staging profile, usually same as target repo')
        parser_create.set_defaults(func=self.create)

        # close
        parser_close = subparsers.add_parser('close', help='Closes a staging repository. After closing, no changes can '
                                                           'be made')
        parser_close.add_argument("repo_id", help='id of the staging repository to be closed')
        parser_close.set_defaults(func=self.close)

        # release
        parser_release = subparsers.add_parser('release', help='Releases a staging repo. Cannot be used for'
                                                               ' user-managed repositories')
        if False:  # to be done
            parser_release.add_argument("-k", "--keep-metadata", action="store_true", default=False,
                                        help="Keep custom maven metadata")

        parser_release.add_argument("repo_id", help='id of staging repository, e.g. releases-1000')
        parser_release.add_argument("--description", help='Description of the release', default='No description')
        parser_release.set_defaults(func=self.release)

        # drop
        parser_drop = subparsers.add_parser('drop', help='Drops a repository. Use carefully!')
        parser_drop.add_argument("-s", "--staging", action="store_true", help='repository is staging')
        parser_drop.add_argument("--description", help='Description of the drop', default='No description')
        parser_drop.add_argument("repo_id", help='id of staging repository, e.g. releases-1000')
        parser_drop.set_defaults(func=self.drop)
        return parser

    def create(self, args):
        """

        :param args:
        :return: staging repository id as string
        """
        if args.staging:
            return self.repository.create_staging_repo(args.repo_id, args.description)
        else:
            raise Exception('Creation of normal repositories not supported yet')

    def close(self, args):
        return self.repository.close_staging_repo(args.repo_id)

    def release(self, args):
        self.repository.release_staging_repo(args.repo_id, args.description)

    def drop(self, args):
        if args.staging:
            self.repository.drop_staging_repo(args.repo_id)
        else:
            raise Exception('Drop of normal repositories not supported yet')
