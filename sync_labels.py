#!/usr/bin/env python3
import sys
import os
import argparse
from github import Github, GithubException, RateLimitExceededException

"""
Sync Github Labels

Synchronize labels idempotently between two Github repositories.
"""


def sync_labels(src_repo, dest_repo, dry_run, force, delete):
    """
    Main subroutine: sync labels between source/destination Github repos

    :param str src_repo: full repo name for source of labels
    :param str dest_repo: full repo name for destination of label actions
    :param bool dry_run: do a dry run, do not perform the actions
    :param bool force: force script to perform the actions without user confirmation
    :param bool delete: delete labels that are in destination but not in source
    """

    # Get PyGithub objects representing repos
    g = Github(get_access_token())
    try:
        s = g.get_repo(src_repo)
    except RateLimitExceededException:
        raise Exception(f"API rate limit hit! Try again later.")
    except GithubException:
        raise Exception(f"Source repo is not a repo: {src_repo}")
    try:
        d = g.get_repo(dest_repo)
    except RateLimitExceededException:
        raise Exception(f"API rate limit hit! Try again later.")
    except GithubException:
        raise Exception(f"Destination repo is not a repo: {dest_repo}")

    # Create list of labels to add/delete
    src_labels = list(s.get_labels())
    src_label_names = set([j.name for j in src_labels])
    dest_labels = list(d.get_labels())
    dest_label_names = set([j.name for j in dest_labels])
    dest_add = sorted(list(src_label_names - dest_label_names))
    dest_del = sorted(list(dest_label_names - src_label_names))

    # Show summary of what actions will be taken, get confirmation
    if len(dest_add) == 0:
        print(f"No labels to create in {dest_repo}")
    else:
        print(f"The following labels will be created in {dest_repo}:")
        for lab in sorted(list(dest_add)):
            print(f" [+] {lab}")

    if delete:
        if len(dest_add) == 0:
            print(f"No labels to delete from {dest_repo}")
        else:
            print(f"The following labels will be deleted in {dest_repo}:")
            for lab in sorted(list(dest_del)):
                print(f" [-] {lab}")

    if not force:
        get_user_confirmation(dry_run)

    # Add new labels
    for name in dest_add:
        print(f"Creating label \"{name}\" in destination repo {dest_repo}...")
        if dry_run:
            print(f"Dry run successful!")
            continue
        label = s.get_label(name)
        color = label.color
        description = label.description
        try:
            import pdb; pdb.set_trace()
            d.create_label(name, color)
            #d.create_label(name, color, description)
            print(f"Success!")
        except GithubException:
            raise Exception(f"Error creating label \"{name}\" in destination repo {dest_repo}")

    # Delete labels
    if delete:
        for name in dest_del:
            print(f"Deleting label \"{name}\" from destination repo {dest_repo}...")
            if dry_run:
                print(f"Dry run successful!")
                continue
            label = rd.get_label(name)
            try:
                label.delete()
                print(f"Success!")
            except GithubException:
                raise Exception(f"Error deleting label \"{name}\" from destination repo {dest_repo}")

    print("Done.")


def get_access_token():
    """Grab github api token from env var"""
    token = os.environ.get("GITHUB_API_KEY", None)
    if token is None:
        raise Exception("No env var GITHUB_API_KEY defined")
    return token


def get_user_confirmation(dry_run):
    """Make sure user is ok to proceed"""
    confirm = ""
    if dry_run:
        confirm = "This script is in dry-run mode. No changes will be made to remotes.\n"
    confirm += "Okay to proceed? (Type 'y' or 'yes' to confirm):\n"
    response = input(confirm)
    if response.lower() not in ["y", "yes"]:
        print("You safely aborted the label sync operation.")
        sys.exit(0)


def main(sysargs=sys.argv[1:]):

    parser = get_argument_parser(sysargs)

    # Make sure the user provided SOME arguments
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Parse the arguments
    args = parser.parse_args(sysargs)

    print(f"Syncing labels from {args.src} to {args.dest}")
    sync_labels(args.src, args.dest, args.dry_run, args.force, args.delete)


def get_argument_parser(sysargs):
    """Assemble and return an argument parser object"""

    parser = argparse.ArgumentParser(prog="Sync Github Labels")
    parser.add_argument(
        "src",
        metavar="source_repo",
        help="Source Github repo for label sync process, in the form username/reponame or orgname/reponame",
    )
    parser.add_argument(
        "dest",
        metavar="destination_repo",
        help="Destination Github repo for label sync process, in the form username/reponame or orgname/reponame",
    )
    parser.add_argument("--dry-run", "-n", help="Do a dry run", action="store_true")
    parser.add_argument(
        "--delete",
        "-d",
        help="Delete labels that are in destination repo and not in source repo",
        action="store_true",
    )
    parser.add_argument(
        "--force",
        "-f",
        help="Perform label sync without waiting for user confirmation",
        action="store_true",
    )
    return parser


if __name__ == "__main__":
    main()
