from __future__ import print_function

import argparse
import json
import sys

import repositorytools
from repositorytools.cli.common import CLI
from repositorytools.lib.repository import logger

__all__ = ['ArtifactCLI', 'artifact_cli']


class ArtifactCLI(CLI):
    def _get_parser(self):
        parser = argparse.ArgumentParser(description='A command line tool for working with artifacts')
        subparsers = parser.add_subparsers()

        # upload
        subparser = subparsers.add_parser('upload', help='Uploads an artifact to repository, can detect name and'
                                                             ' version from filename')
        subparser.add_argument("-s", "--staging", action="store_true", default=False,
                            help="Uploads to a newly created staging repository which targets given repository")
        subparser.add_argument("-x", "--use-existing", action="store_true", default=False,
                            help="To be used with -s, doesn't create a new repo, but uploads directly to an existing"
                                 "staging repo")
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

        # resolve
        subparser = subparsers.add_parser('resolve', help="Resolves artifacts' URLs")
        subparser.add_argument("repo_id", help="id of repository containing the artifact")
        subparser.add_argument("coordinates", help="group:artifact:version[:classifier[:extension]]", nargs='+')
        subparser.set_defaults(func=self.resolve)
        return parser

    def resolve(self, args):
        artifacts = [ repositorytools.RemoteArtifact.from_repo_id_and_coordinates(args.repo_id, coordinates_item)
                      for coordinates_item in args.coordinates ]

        for artifact in artifacts:
            self.repository.resolve_artifact(artifact)

        output = '\n'.join(artifact.url for artifact in artifacts)
        print(output)
        return output

    def upload(self, args):
        try:
            artifact = repositorytools.LocalArtifact(local_path=args.local_file, group=args.group,
                                                     artifact=args.artifact, version=args.version)
        except repositorytools.NameVerDetectionError as e:
            logger.exception('Unable to create instance of local artifact: %s', e)
            sys.exit(1)

        if args.staging:
            if not args.use_existing:
                return self.repository.upload_artifacts_to_new_staging([artifact], args.repo_id, True,
                                                                       description=args.description,
                                                                       upload_filelist=args.upload_filelist)
            else:
                return self.repository.upload_artifacts_to_staging([artifact], args.repo_id, True,
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


artifact_cli = ArtifactCLI()


if __name__ == '__main__':
    artifact_cli()
