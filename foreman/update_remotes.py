#!/usr/bin/env python3
"""
Update git remotes to point forked repositories.

This script:
1. Renames the current 'origin' remote to 'upstream'
2. Adds a new 'origin' remote pointing to your fork

Usage:
    # Local repositories
    python update_remotes.py --repos /path/to/repo1 /path/to/repo2 --fork-user your-github-username

    # Using a config file
    python update_remotes.py --config repos.txt --fork-user your-github-username

    # Remote repositories via SSH
    python update_remotes.py --remote-dir /home/user/projects --remote-host server.example.com --fork-user your-github-username

    # Force SSH or HTTPS format
    python update_remotes.py --config repos.txt --fork-user your-github-username --url-format ssh
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List
import re


class GitRemoteUpdater:
    def __init__(self, fork_user: str, dry_run: bool = False, url_format: str = None,
                 remote_host: str = None, ssh_user: str = None):
        self.fork_user = fork_user
        self.dry_run = dry_run
        self.url_format = url_format  # 'ssh', 'https', or None (auto-detect)
        self.remote_host = remote_host
        self.ssh_user = ssh_user
        self.is_remote = remote_host is not None

    def run_git_command(self, repo_path: Path, command: List[str]) -> tuple[bool, str]:
        """Run a git command in the specified repository (local or remote via SSH)."""
        if self.is_remote:
            # Build SSH command
            ssh_host = f"{self.ssh_user}@{self.remote_host}" if self.ssh_user else self.remote_host
            # Escape quotes in git command for remote execution
            git_cmd = " ".join([f"'{arg}'" if " " in arg else arg for arg in command])
            ssh_command = ["ssh", ssh_host, f"cd '{repo_path}' && git {git_cmd}"]

            try:
                result = subprocess.run(
                    ssh_command,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return True, result.stdout.strip()
            except subprocess.CalledProcessError as e:
                return False, e.stderr.strip()
        else:
            # Local execution
            try:
                result = subprocess.run(
                    ["git"] + command,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return True, result.stdout.strip()
            except subprocess.CalledProcessError as e:
                return False, e.stderr.strip()

    def get_remote_url(self, repo_path: Path, remote: str = "origin") -> str:
        """Get the URL of a remote."""
        success, output = self.run_git_command(repo_path, ["remote", "get-url", remote])
        if success:
            return output
        return ""

    def extract_repo_name(self, url: str) -> str:
        """Extract repository name from GitHub URL."""
        # Handle both SSH and HTTPS URLs
        # SSH: git@github.com:user/repo.git
        # HTTPS: https://github.com/user/repo.git
        patterns = [
            r'github\.com[:/](?:[\w-]+)/([\w.-]+?)(?:\.git)?$',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise ValueError(f"Could not extract repo name from URL: {url}")

    def build_fork_url(self, original_url: str) -> str:
        """Build the fork URL based on the original URL format or specified format."""
        repo_name = self.extract_repo_name(original_url)

        # If url_format is explicitly set, use it
        if self.url_format == "ssh":
            return f"git@github.com:{self.fork_user}/{repo_name}.git"
        elif self.url_format == "https":
            return f"https://github.com/{self.fork_user}/{repo_name}.git"

        # Otherwise, auto-detect from original URL and maintain the same format
        if original_url.startswith("git@github.com:"):
            return f"git@github.com:{self.fork_user}/{repo_name}.git"
        elif original_url.startswith("https://"):
            return f"https://github.com/{self.fork_user}/{repo_name}.git"
        else:
            # Default to SSH
            return f"git@github.com:{self.fork_user}/{repo_name}.git"

    def check_remote_path_exists(self, repo_path: Path) -> bool:
        """Check if a path exists on the remote host via SSH."""
        ssh_host = f"{self.ssh_user}@{self.remote_host}" if self.ssh_user else self.remote_host
        try:
            result = subprocess.run(
                ["ssh", ssh_host, f"test -d '{repo_path}' && echo 'exists'"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.strip() == "exists"
        except subprocess.CalledProcessError:
            return False

    def update_repo(self, repo_path: Path) -> bool:
        """Update a single repository's remotes."""
        if not self.is_remote:
            repo_path = repo_path.resolve()

        # Check if repository exists
        if self.is_remote:
            if not self.check_remote_path_exists(repo_path):
                print(f"❌ Error: Repository path does not exist on remote: {repo_path}")
                return False
            git_dir = f"{repo_path}/.git"
            if not self.check_remote_path_exists(Path(git_dir)):
                print(f"❌ Error: Not a git repository on remote: {repo_path}")
                return False
        else:
            if not repo_path.exists():
                print(f"❌ Error: Repository path does not exist: {repo_path}")
                return False
            if not (repo_path / ".git").exists():
                print(f"❌ Error: Not a git repository: {repo_path}")
                return False

        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Processing: {repo_path}")

        # Get current origin URL
        original_url = self.get_remote_url(repo_path, "origin")
        if not original_url:
            print(f"  ⚠️  Warning: No 'origin' remote found, skipping")
            return False

        print(f"  Current origin: {original_url}")

        # Check if upstream already exists
        upstream_url = self.get_remote_url(repo_path, "upstream")
        if upstream_url:
            print(f"  ⚠️  Warning: 'upstream' remote already exists: {upstream_url}")
            print(f"  Skipping this repository to avoid conflicts")
            return False

        # Build fork URL
        try:
            fork_url = self.build_fork_url(original_url)
        except ValueError as e:
            print(f"  ❌ Error: {e}")
            return False

        print(f"  New origin (fork): {fork_url}")
        print(f"  New upstream: {original_url}")

        if self.dry_run:
            print(f"  ✓ Would update remotes (dry run mode)")
            return True

        # Rename origin to upstream
        success, output = self.run_git_command(repo_path, ["remote", "rename", "origin", "upstream"])
        if not success:
            print(f"  ❌ Failed to rename origin to upstream: {output}")
            return False

        # Add new origin pointing to fork
        success, output = self.run_git_command(repo_path, ["remote", "add", "origin", fork_url])
        if not success:
            print(f"  ❌ Failed to add new origin: {output}")
            # Try to restore original state
            self.run_git_command(repo_path, ["remote", "rename", "upstream", "origin"])
            return False

        # Verify the changes
        success, output = self.run_git_command(repo_path, ["remote", "-v"])
        if success:
            print(f"  ✓ Successfully updated remotes:")
            for line in output.split('\n'):
                print(f"    {line}")

        return True


def read_repos_from_file(file_path: Path) -> List[Path]:
    """Read repository paths from a file (one per line)."""
    repos = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                repos.append(Path(line))
    return repos


def discover_remote_repos(remote_host: str, remote_dir: str, ssh_user: str = None) -> List[Path]:
    """Discover git repositories in a remote directory."""
    ssh_host = f"{ssh_user}@{remote_host}" if ssh_user else remote_host

    # Find all directories containing .git subdirectory
    find_command = f"find '{remote_dir}' -maxdepth 2 -type d -name '.git' -exec dirname {{}} \\;"

    try:
        result = subprocess.run(
            ["ssh", ssh_host, find_command],
            capture_output=True,
            text=True,
            check=True
        )
        repos = []
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line:
                repos.append(Path(line))
        return repos
    except subprocess.CalledProcessError as e:
        print(f"Error discovering repositories on remote host: {e.stderr}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Update git remotes to point to forked repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update specific local repositories (auto-detect URL format)
  %(prog)s --fork-user myusername --repos /path/to/repo1 /path/to/repo2

  # Update repositories listed in a file
  %(prog)s --fork-user myusername --config repos.txt

  # Auto-discover and update repos in remote directory via SSH
  %(prog)s --fork-user myusername --remote-host user@server.com --remote-dir /home/user/projects

  # Remote execution with separate SSH user flag
  %(prog)s --fork-user myusername --remote-host server.com --ssh-user myuser --remote-dir /home/myuser/repos

  # Force SSH format for all fork URLs
  %(prog)s --fork-user myusername --config repos.txt --url-format ssh

  # Force HTTPS format for all fork URLs
  %(prog)s --fork-user myusername --config repos.txt --url-format https

  # Dry run to see what would happen (works with remote too)
  %(prog)s --fork-user myusername --remote-host server.com --remote-dir /repos --dry-run
        """
    )

    parser.add_argument(
        "--fork-user",
        required=True,
        help="Your GitHub username (owner of the forks)"
    )

    repo_group = parser.add_mutually_exclusive_group(required=True)
    repo_group.add_argument(
        "--repos",
        nargs="+",
        type=Path,
        help="List of repository paths to update"
    )
    repo_group.add_argument(
        "--config",
        type=Path,
        help="Path to file containing repository paths (one per line)"
    )
    repo_group.add_argument(
        "--remote-dir",
        type=str,
        help="Auto-discover git repositories in this directory on remote host (requires --remote-host)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    parser.add_argument(
        "--url-format",
        choices=["ssh", "https"],
        help="Force SSH or HTTPS format for fork URLs (default: auto-detect from original URL)"
    )

    parser.add_argument(
        "--remote-host",
        type=str,
        help="Remote SSH host to execute commands on (e.g., user@hostname or hostname)"
    )

    parser.add_argument(
        "--ssh-user",
        type=str,
        help="SSH username for remote host (if not included in --remote-host)"
    )

    args = parser.parse_args()

    # Validate remote-related arguments
    if args.remote_dir and not args.remote_host:
        parser.error("--remote-dir requires --remote-host")

    if args.ssh_user and not args.remote_host:
        parser.error("--ssh-user requires --remote-host")

    # Get list of repositories
    if args.config:
        if not args.config.exists():
            print(f"Error: Config file not found: {args.config}")
            sys.exit(1)
        repos = read_repos_from_file(args.config)
    elif args.remote_dir:
        print(f"Discovering repositories in {args.remote_dir} on {args.remote_host}...")
        repos = discover_remote_repos(args.remote_host, args.remote_dir, args.ssh_user)
        if not repos:
            print(f"Error: No repositories found in {args.remote_dir}")
            sys.exit(1)
        print(f"Found {len(repos)} repositories")
    else:
        repos = args.repos

    if not repos:
        print("Error: No repositories specified")
        sys.exit(1)

    print(f"{'=' * 60}")
    print(f"Git Remote Updater")
    print(f"Fork owner: {args.fork_user}")
    print(f"Repositories to update: {len(repos)}")
    if args.remote_host:
        print(f"Remote host: {args.remote_host}")
        print(f"Execution mode: SSH (remote)")
    else:
        print(f"Execution mode: Local")
    if args.url_format:
        print(f"URL format: {args.url_format.upper()}")
    else:
        print(f"URL format: auto-detect from original URL")
    if args.dry_run:
        print("Mode: DRY RUN (no changes will be made)")
    print(f"{'=' * 60}")

    updater = GitRemoteUpdater(args.fork_user, args.dry_run, args.url_format,
                                args.remote_host, args.ssh_user)

    success_count = 0
    failed_count = 0

    for repo in repos:
        if updater.update_repo(repo):
            success_count += 1
        else:
            failed_count += 1

    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  ✓ Successfully updated: {success_count}")
    print(f"  ❌ Failed or skipped: {failed_count}")
    print(f"{'=' * 60}")

    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
