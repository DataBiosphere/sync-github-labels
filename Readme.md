# Sync Github Labels

This script will synchronize labels idempotently between two Github repositories.

## Before You Begin

Before using this script, it requires the use of a Gitub API key. This can be created
by logging into Github (using an account that has the ability to create/remove labels
from the source and destination repositories), going to Settings > Developer > Access Tokens,
and creating a new access token with the ability to control repositories.

## Basic Usage

Call this script on the command line, and pass it the source and destination repo:

```
./sync_labels.py [--FLAGS] SOURCE_REPO DEST_REPO
```

## Normal Operation

The basic mode of operation is to pass the script the full name of a source repository 
and a destination repository:

```
./sync_labels.py foo/hello-world bar/hello-world
```

## `--dry-run`: Dry Run Mode

To do a dry-run of what actions would be taken by the script, use the `--dry-run` or `-n` flag:

```
./sync_labels.py --dry-run foo/hello-world bar/hello-world
./sync_labels.py -n foo/hello-world bar/hello-world
```

This will run the script but will skip any API calls that create or delete labels.

## `--force`: Non-Interactive Operation

By default this script will print a summary of changes that will be made and will ask the
user to confirm before any actions are taken. To force the script to proceed without waiting
for user confirmation, use the `--force` flag:

```
./sync_labels --force foo/hello-world bar/hello-world
./sync_labels -f foo/hello-world bar/hello-world
```

This will skip all interactive prompts.

## `--delete`: Delete Mode

The default behavior of the script is to look for labels that are in the source repo and 
not in the destination repo. Labels that are in the destination repo but not in the source repo
are ignored.

By adding the `--delete` flag, the script will delete any label that is in the destination repo
that is not in the source repo.

```
./sync_labels --delete foo/hello-world bar/hello-world
./sync_labels -d foo/hello-world bar/hello-world
```

**Warning: This operation is destructive! Make sure to use the `--dry-run` flag first.**
