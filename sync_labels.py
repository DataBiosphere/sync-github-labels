#!/usr/bin/env python3
import sys
import os
import json
import logging
import argparse
from github import Github, GithubException, UnknownObjectException, BadCredentialsException

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
    dst_upd = src_label_names.intersection(dst_label_names)
    dst_del = dst_label_names - src_label_names

    # Show summary of what actions will be taken
    if len(dst_add) > 0:
        print(f"The following labels will be created in {dst_repo}:")
        print_list(list(dst_add), " [+] ")

    if len(dst_upd) > 0:
        print(f"The following labels will be updated in {dst_repo}:")
        print_list(list(dst_upd), " [u] ")

    if delete:
        if len(dst_del) > 0:
            print(f"The following labels will be deleted in {dst_repo}:")
            print_list(list(dst_del), " [-] ")

    # Add new labels
    add_ok = []
    for name in dst_add:
        if dry_run:
            add_ok.append(name)
        else:
            print_sameline("Adding label: " + name)
            label = src.get_label(name)
            color = label.color
            description = label.description
            try:
                dst.create_label(name, color, description)
            except GithubException:
                logging.exception(f"Error adding label: {name}")
                sys.exit(1)

    # Update existing labels
    upd_ok = []
    for name in dst_upd:
        if dry_run:
            upd_ok.append(name)
        else:
            print_sameline("Updating label: " + name)
            label = src.get_label(name)
            dst_label = dst.get_label(name)
            color = label.color
            description = label.description
            try:
                dst_label.edit(name, color, description)
            except GithubException:
                logging.exception(f"Error updating label: {name}")
                sys.exit(1)

    # Delete labels
    del_ok = []
    if delete:
        for name in dst_del:
            if dry_run:
                del_ok.append(name)
            else:
                print_sameline("Deleting label: " + name)
                label = dst.get_label(name)
                try:
                    label.delete()
                except GithubException:
                    logging.exception(f"Error deleting label: {name}")
                    sys.exit(1)

    if not dry_run:
        print_sameline("Done.", last_line=True)
        sys.exit(0)


def print_sameline(msg, last_line=False):
    sys.stdout.write("\033[K") # Clear prior printed line
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
        logger.info(f"{bull}{item}")


def main(sysargs=sys.argv[1:]):

    parser = get_argument_parser(sysargs)
    args = parser.parse_args(sysargs)

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
    main()
