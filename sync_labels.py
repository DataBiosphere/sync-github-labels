#!/usr/bin/env python3
import sys
import os
import logging
import argparse
from github import (
    Github,
    GithubObject,
    UnknownObjectException,
)

"""
Sync Github Labels

Synchronize labels idempotently between two Github repositories.
"""


# Set up logging
log_name = "sync_labels.log"
fh = logging.FileHandler(log_name)
fh.setFormatter(logging.Formatter(fmt="[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(logging.Formatter(fmt="%(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[fh, sh])
logger = logging.getLogger(os.path.basename(__file__))


def sync_labels(src_repo, dst_repo, dry_run, delete):
    """
    Main subroutine: sync labels between source/destination Github repos

    :param src_repo: full repo name for source of labels
    :param dst_repo: full repo name for destination of label actions
    :param dry_run: do a dry run, do not perform the actions
    :param delete: delete labels that are in destination but not in source
    """

    # Get PyGithub objects representing repos
    gh = Github(get_access_token())
    try:
        src = gh.get_repo(src_repo)
    except UnknownObjectException as e:
        raise RuntimeError("The specified source repository does not exist.", src_repo)
    try:
        dst = gh.get_repo(dst_repo)
    except UnknownObjectException as e:
        raise RuntimeError("The destination repository specified does not exist.", dst_repo)

    # Create list of labels to add/delete
    src_labels = list(src.get_labels())
    src_label_names = {j.name for j in src_labels}
    dst_labels = list(dst.get_labels())
    dst_label_names = {j.name for j in dst_labels}
    dst_add = src_label_names - dst_label_names
    dst_update = src_label_names.intersection(dst_label_names)
    dst_delete = dst_label_names - src_label_names if delete else set()

    for action, labels, symbol in (('created', dst_add, '+'),
                                   ('updated', dst_update, 'u'),
                                   ('deleted', dst_delete, '-')):
        if len(labels) > 0:
            print(f"The following labels will be {action} in {dst_repo}:")
            print_list(list(labels), symbol)

    fails = []

    for action, labels, function in (('Adding', dst_add, add_label),
                                     ('Updating', dst_update, update_label),
                                     ('Deleting', dst_delete, delete_label)):
        for name in labels:
            print_sameline(f'{action} label: {name}')
            if not dry_run:
                try:
                    function(name, src, dst)
                except Exception:
                    logging.exception(f'Error {action.lower()} label: {name}')
                    fails.append((action, name))
    print_sameline("Done.", last_line=True)

    if fails:
        print('The following labels failed:', file=sys.stderr)
    for action, name in fails:
        print(f'{action} {repr(name)}', file=sys.stderr)


def add_label(name, src, dst):
    label = src.get_label(name)
    color = label.color
    description = label.description or GithubObject.NotSet
    dst.create_label(name, color, description)


def update_label(name, src, dst):
    label = src.get_label(name)
    dst_label = dst.get_label(name)
    color = label.color
    description = label.description or GithubObject.NotSet
    dst_label.edit(name, color, description)


def delete_label(name, src, dst):
    label = dst.get_label(name)
    label.delete()


def print_sameline(msg, last_line=False):
    sys.stdout.write("\033[K")  # Clear prior printed line
    if not last_line:
        print(msg, end="\r")
    else:
        print(msg)


def get_access_token():
    """Grab Github API token from environment variable"""
    try:
        api_key = os.environ["GITHUB_API_KEY"]
    except KeyError:
        raise RuntimeError("No environment variable GITHUB_API_KEY defined")
    return api_key


def print_list(lst, bull):
    """Print a list, one item per line, starting with string bull"""
    for item in sorted(lst):
        logger.info(f" [{bull}] {item}")


def main(args):

    parser = get_argument_parser(args)
    args = parser.parse_args(args)

    logger.info("="*30)
    logger.info(f"{os.path.basename(__file__)}: Syncing labels from {args.src} to {args.dst}")
    sync_labels(args.src, args.dst, args.dry_run, args.delete)


def get_argument_parser(sysargs):

    parser = argparse.ArgumentParser(prog="Sync Github Labels")
    parser.add_argument(
        "src",
        metavar="source_repo",
        help="Source Github repo for label sync process, in the form username/reponame or orgname/reponame",
    )
    parser.add_argument(
        "dst",
        metavar="destination_repo",
        help="Destination Github repo for label sync process, in the form username/reponame or orgname/reponame",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        help="Do a dry run (no labels are changed in the destination repo)",
        action="store_true",
    )
    parser.add_argument(
        "--delete",
        "-d",
        help="Delete labels that are in destination repo and not in source repo",
        action="store_true",
    )
    return parser


if __name__ == "__main__":
    main(sys.argv[1:])
