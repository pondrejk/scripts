#!/usr/bin/env python3
"""
Display git repository status in a formatted table.

This script:
1. Discovers git repositories in a specified directory
2. Gathers status information (branch, remote tracking, ahead/behind counts, uncommitted changes)
3. Displays the information in a color-coded table
4. Optionally auto-syncs repositories that are behind with no uncommitted changes

Usage:
    # Remote usage
    python git_repo_status.py --remote-host server.example.com --remote-dir /home/user/projects

    # With SSH user
    python git_repo_status.py --remote-host server.example.com --ssh-user myuser --remote-dir /home/user/projects

    # Local usage
    python git_repo_status.py --dir /path/to/projects

    # Custom search depth
    python git_repo_status.py --remote-host server.example.com --remote-dir /projects --max-depth 3

    # Auto-sync repos that are behind with no uncommitted changes
    python git_repo_status.py --dir /path/to/projects --auto-sync
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re


class Color:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'


class GitRepoStatusChecker:
    """Check and display git repository status for multiple repositories."""

    def __init__(self, remote_host: Optional[str] = None, ssh_user: Optional[str] = None,
                 max_depth: int = 2, auto_sync: bool = False):
        """
        Initialize the status checker.

        Args:
            remote_host: Remote SSH host to execute commands on (None for local)
            ssh_user: SSH username for remote host
            max_depth: Maximum directory depth for repository search
            auto_sync: Automatically pull --rebase repos that are behind with no changes
        """
        self.remote_host = remote_host
        self.ssh_user = ssh_user
        self.is_remote = remote_host is not None
        self.max_depth = max_depth
        self.auto_sync = auto_sync

    def run_git_command(self, repo_path: Path, command: List[str]) -> Tuple[bool, str]:
        """
        Run a git command in the specified repository (local or remote via SSH).

        Args:
            repo_path: Path to the git repository
            command: Git command arguments (without 'git' prefix)

        Returns:
            Tuple of (success: bool, output: str)
        """
        if self.is_remote:
            # Build SSH command
            ssh_host = f"{self.ssh_user}@{self.remote_host}" if self.ssh_user else self.remote_host
            # Escape quotes in git command for remote execution
            git_cmd = " ".join([f"'{arg}'" if " " in arg else arg for arg in command])
            cmd = ["ssh", ssh_host, f"cd '{repo_path}' && git {git_cmd}"]
        else:
            # Local execution
            cmd = ["git", "-C", str(repo_path)] + command

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()

    def discover_repos(self, directory: str) -> List[Path]:
        """
        Discover git repositories in the specified directory.

        Args:
            directory: Directory path to search in

        Returns:
            List of paths to git repositories
        """
        if self.is_remote:
            return self._discover_remote_repos(directory)
        else:
            return self._discover_local_repos(directory)

    def _discover_remote_repos(self, remote_dir: str) -> List[Path]:
        """Discover git repositories in a remote directory via SSH."""
        ssh_host = f"{self.ssh_user}@{self.remote_host}" if self.ssh_user else self.remote_host

        # Find all directories containing .git subdirectory
        find_command = f"find '{remote_dir}' -maxdepth {self.max_depth} -type d -name '.git' -exec dirname {{}} \\;"

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

    def _discover_local_repos(self, local_dir: str) -> List[Path]:
        """Discover git repositories in a local directory."""
        try:
            result = subprocess.run(
                ["find", local_dir, "-maxdepth", str(self.max_depth), "-type", "d", "-name", ".git"],
                capture_output=True,
                text=True,
                check=True
            )
            repos = []
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line:
                    # Get parent directory of .git
                    repos.append(Path(line).parent)
            return repos
        except subprocess.CalledProcessError as e:
            print(f"Error discovering repositories: {e.stderr}")
            return []

    def get_repo_status(self, repo_path: Path) -> Dict[str, any]:
        """
        Get status information for a single repository.

        Args:
            repo_path: Path to the git repository

        Returns:
            Dictionary with status information:
            {
                'name': str,
                'branch': str,
                'remote_branch': str,
                'ahead': int,
                'behind': int,
                'changes': int,
                'error': str (if any),
                'synced': bool
            }
        """
        status = {
            'name': repo_path.name,
            'branch': '',
            'remote_branch': '',
            'ahead': 0,
            'behind': 0,
            'changes': 0,
            'error': None,
            'synced': False
        }

        # Use batched execution for both remote and local
        return self._get_repo_status_batch(repo_path)

    def _get_repo_status_batch(self, repo_path: Path) -> Dict[str, any]:
        """
        Get status information using a single batched call (works for both local and remote).

        Args:
            repo_path: Path to the git repository

        Returns:
            Dictionary with status information
        """
        status = {
            'name': repo_path.name,
            'branch': '',
            'remote_branch': '',
            'ahead': 0,
            'behind': 0,
            'changes': 0,
            'error': None,
            'synced': False
        }

        # Build a shell script that runs all git commands in one go
        # Using a delimiter to separate outputs
        delimiter = "---GIT-STATUS-DELIMITER---"
        batch_script = f"""
cd '{repo_path}' && {{
    git rev-parse --abbrev-ref HEAD 2>&1
    echo '{delimiter}'
    git rev-parse --abbrev-ref @{{upstream}} 2>&1
    echo '{delimiter}'
    git status -sb 2>&1
    echo '{delimiter}'
    git status --porcelain 2>&1
}}
"""

        try:
            if self.is_remote:
                # Remote execution via SSH
                ssh_host = f"{self.ssh_user}@{self.remote_host}" if self.ssh_user else self.remote_host
                result = subprocess.run(
                    ["ssh", ssh_host, batch_script],
                    capture_output=True,
                    text=True,
                    check=False  # Don't raise on non-zero exit
                )
            else:
                # Local execution via bash
                result = subprocess.run(
                    ["bash", "-c", batch_script],
                    capture_output=True,
                    text=True,
                    check=False  # Don't raise on non-zero exit
                )

            # Split output by delimiter
            parts = result.stdout.split(delimiter)
            if len(parts) < 4:
                status['error'] = "Failed to parse batch output"
                return status

            # Parse branch
            branch = parts[0].strip()
            if branch and not branch.startswith("fatal:"):
                status['branch'] = branch
            else:
                status['error'] = "Failed to get branch"
                return status

            # Parse remote tracking branch
            remote_branch = parts[1].strip()
            if remote_branch and not remote_branch.startswith("fatal:"):
                status['remote_branch'] = remote_branch
            else:
                status['remote_branch'] = None

            # Parse ahead/behind from status -sb
            if status['remote_branch']:
                status_output = parts[2].strip()
                if status_output and not status_output.startswith("fatal:"):
                    ahead, behind = self._parse_branch_status(status_output)
                    status['ahead'] = ahead
                    status['behind'] = behind

            # Parse uncommitted changes
            changes_output = parts[3].strip()
            if changes_output and not changes_output.startswith("fatal:"):
                lines = [line for line in changes_output.split('\n') if line.strip()]
                status['changes'] = len(lines)

        except subprocess.CalledProcessError as e:
            status['error'] = f"SSH error: {e.stderr}"

        return status

    def _parse_branch_status(self, status_output: str) -> Tuple[int, int]:
        """
        Parse git status -sb output to extract ahead/behind counts.

        Args:
            status_output: Output from git status -sb

        Returns:
            Tuple of (ahead: int, behind: int)
        """
        ahead = 0
        behind = 0

        # Look for pattern: ## branch...remote [ahead X, behind Y]
        # or: ## branch...remote [ahead X]
        # or: ## branch...remote [behind Y]
        match = re.search(r'\[ahead (\d+)(?:, behind (\d+))?\]', status_output)
        if match:
            ahead = int(match.group(1))
            if match.group(2):
                behind = int(match.group(2))
            return ahead, behind

        match = re.search(r'\[behind (\d+)\]', status_output)
        if match:
            behind = int(match.group(1))
            return ahead, behind

        return ahead, behind

    def should_sync(self, status: Dict[str, any]) -> bool:
        """
        Check if a repository should be auto-synced.

        Conditions:
        - Has a remote tracking branch
        - Is behind origin
        - Is not ahead of origin
        - Has no uncommitted changes
        - No errors

        Args:
            status: Repository status dictionary

        Returns:
            True if the repository should be synced
        """
        return (
            self.auto_sync and
            status['remote_branch'] is not None and
            status['behind'] > 0 and
            status['ahead'] == 0 and
            status['changes'] == 0 and
            status['error'] is None
        )

    def sync_repo(self, repo_path: Path) -> Tuple[bool, str]:
        """
        Sync a repository using git pull --rebase.

        Args:
            repo_path: Path to the git repository

        Returns:
            Tuple of (success: bool, message: str)
        """
        success, output = self.run_git_command(repo_path, ["pull", "--rebase"])
        if success:
            return True, "Synced successfully"
        else:
            return False, f"Sync failed: {output}"


def get_status_symbol(status: Dict[str, any]) -> str:
    """
    Get status symbol based on repository state.

    Args:
        status: Repository status dictionary

    Returns:
        Unicode symbol representing the status
    """
    if status['error']:
        return '⚠️'
    if not status['remote_branch']:
        return '⚠️'
    if status['ahead'] > 0 and status['behind'] > 0:
        return '↕'  # Diverged
    if status['ahead'] > 0:
        return '↑'  # Ahead
    if status['behind'] > 0:
        return '↓'  # Behind
    return '✓'  # Synced


def get_status_color(status: Dict[str, any]) -> str:
    """
    Get ANSI color code for status.

    Args:
        status: Repository status dictionary

    Returns:
        ANSI color code string
    """
    if status['error']:
        return Color.GRAY
    if not status['remote_branch']:
        return Color.GRAY
    if status['ahead'] > 0 and status['behind'] > 0:
        return Color.RED  # Diverged
    if status['ahead'] > 0:
        return Color.CYAN  # Ahead
    if status['behind'] > 0:
        return Color.YELLOW  # Behind
    return Color.GREEN  # Synced


def format_status_table(statuses: List[Dict[str, any]], remote_host: Optional[str],
                       directory: str) -> str:
    """
    Format repository statuses into a table.

    Args:
        statuses: List of repository status dictionaries
        remote_host: Remote host name (None for local)
        directory: Directory that was searched

    Returns:
        Formatted table string
    """
    if not statuses:
        return "No repositories found."

    # Calculate column widths
    repo_width = max(len(s['name']) for s in statuses)
    repo_width = max(repo_width, len("Repository"))

    branch_width = max(len(s['branch']) for s in statuses)
    branch_width = max(branch_width, len("Branch"))

    # Build table
    lines = []
    separator = "=" * 80
    lines.append(separator)
    lines.append("Git Repository Status")

    location = f"Remote: {remote_host}" if remote_host else "Local"
    lines.append(f"{location} | Directory: {directory} | Found: {len(statuses)} repos")
    lines.append(separator)
    lines.append("")

    # Header
    header = (f"{'Repository':<{repo_width}}  {'Branch':<{branch_width}}  "
             f"Status   Ahead  Behind  Changes")
    lines.append(header)
    lines.append("-" * 80)

    # Count statuses for summary
    synced = ahead = behind = diverged = no_remote = 0

    # Data rows
    for status in statuses:
        symbol = get_status_symbol(status)
        color = get_status_color(status)

        # Count for summary
        if status['error'] or not status['remote_branch']:
            no_remote += 1
        elif status['ahead'] > 0 and status['behind'] > 0:
            diverged += 1
        elif status['ahead'] > 0:
            ahead += 1
        elif status['behind'] > 0:
            behind += 1
        else:
            synced += 1

        repo_name = status['name']
        branch = status['branch']

        ahead_str = str(status['ahead']) if status['remote_branch'] else '—'
        behind_str = str(status['behind']) if status['remote_branch'] else '—'

        # Highlight changes if not 0
        changes_count = status['changes']
        if changes_count > 0:
            changes_str = f"{Color.YELLOW}{changes_count}{Color.END}"
        else:
            changes_str = str(changes_count)

        # Add sync indicator if repo was synced
        sync_indicator = f"  {Color.CYAN}[auto-synced]{Color.END}" if status.get('synced', False) else ""

        row = (f"{repo_name:<{repo_width}}  {branch:<{branch_width}}  "
              f"{color}{symbol:<6}{Color.END}  "
              f"{ahead_str:<5}  {behind_str:<6}  {changes_str}{sync_indicator}")
        lines.append(row)

    lines.append("-" * 80)
    lines.append("")

    # Legend
    lines.append("Legend:")
    lines.append(f"  {Color.GREEN}✓{Color.END} Synced    "
                f"{Color.CYAN}↑{Color.END} Ahead    "
                f"{Color.YELLOW}↓{Color.END} Behind    "
                f"{Color.RED}↕{Color.END} Diverged    "
                f"{Color.GRAY}⚠️{Color.END}  No remote tracking")
    lines.append("")

    # Summary
    summary_parts = []
    if synced > 0:
        summary_parts.append(f"{synced} synced")
    if ahead > 0:
        summary_parts.append(f"{ahead} ahead")
    if behind > 0:
        summary_parts.append(f"{behind} behind")
    if diverged > 0:
        summary_parts.append(f"{diverged} diverged")
    if no_remote > 0:
        summary_parts.append(f"{no_remote} no remote")

    summary = "Summary: " + ", ".join(summary_parts)
    lines.append(summary)
    lines.append(separator)

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Display git repository status in a formatted table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Remote usage
  %(prog)s --remote-host server.example.com --remote-dir /home/user/projects

  # With SSH user
  %(prog)s --remote-host server.example.com --ssh-user myuser --remote-dir /home/user/projects

  # Local usage
  %(prog)s --dir /path/to/projects

  # Custom search depth
  %(prog)s --remote-host server.example.com --remote-dir /projects --max-depth 3

  # Auto-sync repos that are behind with no uncommitted changes
  %(prog)s --dir /path/to/projects --auto-sync
        """
    )

    # Directory arguments (mutually exclusive)
    dir_group = parser.add_mutually_exclusive_group(required=True)
    dir_group.add_argument(
        "--dir",
        type=str,
        help="Local directory path to search for repositories"
    )
    dir_group.add_argument(
        "--remote-dir",
        type=str,
        help="Remote directory path to search for repositories (requires --remote-host)"
    )

    # Remote host arguments
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

    # Search depth
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Maximum directory depth for repository search (default: 2)"
    )

    # Auto-sync option
    parser.add_argument(
        "--auto-sync",
        action="store_true",
        help="Automatically sync repos that are behind with no uncommitted changes using git pull --rebase"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.remote_dir and not args.remote_host:
        parser.error("--remote-dir requires --remote-host")

    if args.ssh_user and not args.remote_host:
        parser.error("--ssh-user requires --remote-host")

    if args.dir and args.remote_host:
        parser.error("--dir cannot be used with --remote-host (use --remote-dir instead)")

    # Determine directory
    directory = args.remote_dir if args.remote_dir else args.dir

    # Create status checker
    checker = GitRepoStatusChecker(
        remote_host=args.remote_host,
        ssh_user=args.ssh_user,
        max_depth=args.max_depth,
        auto_sync=args.auto_sync
    )

    # Discover repositories
    location = f"remote host {args.remote_host}" if args.remote_host else "local directory"
    print(f"Discovering git repositories in {directory} on {location}...")
    repos = checker.discover_repos(directory)

    if not repos:
        print(f"No git repositories found in {directory}")
        sys.exit(1)

    print(f"Found {len(repos)} repositories")
    print("Gathering status information...")

    # Get status for each repository
    statuses = []
    repos_to_sync = []
    for repo in sorted(repos):
        status = checker.get_repo_status(repo)
        statuses.append(status)

        # Check if this repo should be auto-synced
        if checker.should_sync(status):
            repos_to_sync.append((repo, status))

    print()

    # Perform auto-sync if needed
    if repos_to_sync:
        print(f"{Color.CYAN}Auto-syncing {len(repos_to_sync)} repositories...{Color.END}")
        print()
        for repo, status in repos_to_sync:
            print(f"  Syncing {status['name']}...", end=' ', flush=True)
            success, message = checker.sync_repo(repo)
            if success:
                print(f"{Color.GREEN}✓{Color.END} {message}")
                # Update status to reflect the sync
                status['synced'] = True
                # Re-check status after sync
                new_status = checker.get_repo_status(repo)
                status['ahead'] = new_status['ahead']
                status['behind'] = new_status['behind']
                status['changes'] = new_status['changes']
            else:
                print(f"{Color.RED}✗{Color.END} {message}")
        print()

    # Display table
    table = format_status_table(statuses, args.remote_host, directory)
    print(table)


if __name__ == "__main__":
    main()
