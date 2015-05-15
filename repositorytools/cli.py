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
    """
    Base class for cli
    """
    __metaclass__ = ABCMeta

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
        # in tests we don't use 'str(sys.argv), so we can log actual arguments
        used_args = args or sys.argv[1:]
        logger.info('Started %s, with arguments %s', sys.argv[0], str(used_args))

        """
        This runs the function that is assigned to the sub-command by calling of set_defaults
        """
        return args_namespace.func(args_namespace)


class ArtifactCLI(CLI):
    def _get_parser(self):
        parser = argparse.ArgumentParser(description='A command line tool for working with artifacts')
        subparsers = parser.add_subparsers()

        # upload
        subparser = subparsers.add_parser('upload', help='Uploads an artifact to repository, can detect name and'
                                                             ' version from filename')
        subparser.add_argument("-s", "--staging", action="store_true", dest="staging", default=False,
                            help="Uploads to a newly created staging repository which targets given repository")
        subparser.add_argument("--upload-filelist", action="store_true", default=False, help="uploads list of uploaded "
                                                                                                 "files")
        subparser.add_argument("--artifact", help="name of artifact, if omitted, will be detected from filename")
        subparser.add_argument("--version", help="version of artifact, if omitted, will be detected from filename")
        subparser.add_argument("-d", "--description", dest="description", default='No description',
                                   help="Description of a staging repository")

        subparser.add_argument("local_file", help="path to an artifact on your machine")
        subparser.add_argument("repo_id", help="id of target repository")
        subparser.add_argument("group", help="artifact group")
        subparser.set_defaults(func=self.upload)

        # delete
        subparser = subparsers.add_parser('delete', help='Deletes an artifact from repository')
        subparser.add_argument("url", help="URL of the artifact")
        subparser.set_defaults(func=self.delete)

        # get metadata
        subparser = subparsers.add_parser('get-metadata', help="Prints artifact's metadata")
        subparser.add_argument("repo_id", help="id of repository containing the artifact")
        subparser.add_argument("coordinates", help="group:artifact:version[:classifier[:extension]]")
        subparser.set_defaults(func=self.get_metadata)

        # set metadata
        subparser = subparsers.add_parser('set-metadata', help="Sets artifact's metadata")
        subparser.add_argument("metadata", help="Dict in JSON format. All keys and values have to be strings,"
                                                          "e.g. '{\"key1\":\"value1\",\"key2\":\"value2\"}'")
        subparser.add_argument("repo_id", help="id of repository containing the artifact")
        subparser.add_argument("coordinates", help="group:artifact:version[:classifier[:extension]]", nargs='+')

        subparser.set_defaults(func=self.set_metadata)
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
        metadata = json.loads(args.metadata)
        for coordinates_item in args.coordinates:
            artifact = repositorytools.RemoteArtifact.from_repo_id_and_coordinates(args.repo_id, coordinates_item)
            self.repository.set_artifact_metadata(artifact, metadata)


class RepoCLI(CLI):
    def _get_parser(self):
        parser = argparse.ArgumentParser(description='A command line tool for working with repositories')
        subparsers = parser.add_subparsers()

        # create
        subparser = subparsers.add_parser('create', help='Creates a repository')
        subparser.add_argument("-s", "--staging", action="store_true", help='Creates a staging repository with'
                                                                         ' target to given repo')
        subparser.add_argument("-d", "--description", help='description of staged repo', default='no description')
        subparser.add_argument("repo_id", help='id of the repository, if used with -s, it is id of staging profile, '
                                               'usually same as target repo')
        subparser.set_defaults(func=self.create)

        # close
        subparser = subparsers.add_parser('close', help='Closes a staging repository. After closing, no changes can '
                                                           'be made')
        subparser.add_argument("repo_id", help='id of the staging repository to be closed')
        subparser.set_defaults(func=self.close)

        # release
        subparser = subparsers.add_parser('release', help='Releases a staging repo. Cannot be used for'
                                                          ' user-managed repositories')

        subparser.add_argument("-k", "--keep-metadata", action="store_true", default=False,
                                    help="Keep custom maven metadata")

        subparser.add_argument("repo_id", help='id of staging repository, e.g. releases-1000')
        subparser.add_argument("--description", help='Description of the release', default='No description')
        subparser.set_defaults(func=self.release)

        # drop
        subparser = subparsers.add_parser('drop', help='Drops a repository. Use carefully!')
        subparser.add_argument("-s", "--staging", action="store_true", help='repository is staging')
        subparser.add_argument("--description", help='Description of the drop', default='No description')
        subparser.add_argument("repo_id", help='id of staging repository, e.g. releases-1000')
        subparser.set_defaults(func=self.drop)
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
        return self.repository.release_staging_repo(args.repo_id, args.description, keep_metadata=args.keep_metadata)

    def drop(self, args):
        if args.staging:
            self.repository.drop_staging_repo(args.repo_id)
        else:
            raise Exception('Drop of normal repositories not supported yet')
