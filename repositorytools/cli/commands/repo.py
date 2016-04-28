from __future__ import print_function

import argparse
import json

from repositorytools.cli.common import CLI

__all__ = ['RepoCLI', 'repo_cli']


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
        subparser.add_argument("repo_ids", help='id of the staging repository to be closed', nargs='+')
        subparser.set_defaults(func=self.close)

        # release
        subparser = subparsers.add_parser('release', help='Releases a staging repo. Cannot be used for'
                                                          ' user-managed repositories')

        subparser.add_argument("-k", "--keep-metadata", action="store_true", default=False,
                                    help="Keep custom maven metadata")

        subparser.add_argument("repo_ids", help='id of staging repository, e.g. releases-1000',  nargs='+')
        subparser.add_argument("--description", help='Description of the release', default='No description')
        subparser.set_defaults(func=self.release)

        # drop
        subparser = subparsers.add_parser('drop', help='Drops a repository. Use carefully!')
        subparser.add_argument("-s", "--staging", action="store_true", help='repository is staging')
        subparser.add_argument("--description", help='Description of the drop', default='No description')
        subparser.add_argument("repo_ids", help='id of staging repository, e.g. releases-1000',  nargs='+')
        subparser.set_defaults(func=self.drop)

        # list
        subparser = subparsers.add_parser('list', help='Lists all reposititories')
        subparser.add_argument("-s", "--staging", action="store_true", help='List staging repositories instead of normal repositories')
        subparser.add_argument("--output-format", help='Format of the output list', choices=['json', 'ids'])
        subparser.add_argument("--filter", help='JSON-serialized dictionary containing filters, for example \'{"description":"foo"}\'')

        subparser.set_defaults(func=self.list)
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
        return self.repository.close_staging_repos(args.repo_ids)

    def release(self, args):
        for repo_id in args.repo_ids:
            self.repository.release_staging_repo(repo_id, args.description, keep_metadata=args.keep_metadata)

    def drop(self, args):
        if args.staging:
            self.repository.drop_staging_repos(args.repo_ids)
        else:
            raise Exception('Drop of normal repositories not supported yet')

    def list(self, args):
        if args.staging:
            if args.filter:
                filter_dict = json.loads(args.filter)
            else:
                filter_dict = None
            repos = self.repository.list_staging_repos(filter_dict)
        else:
            # repos = self.repository.list_repos(args.filter)
            raise Exception('Listing normal repositories not supported yet')

        if args.output_format == 'json':
            output = json.dumps(repos)
        else:
            output = '\n'.join(repo['repositoryId'] for repo in repos)

        print(output)
        return output


repo_cli = RepoCLI()


if __name__ == '__main__':
    repo_cli()
