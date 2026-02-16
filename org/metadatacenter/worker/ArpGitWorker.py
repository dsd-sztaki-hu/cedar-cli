import os
import subprocess
import time
from typing import List, Tuple

import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.style import Style
from rich.table import Table

from org.metadatacenter.util.Const import Const
from org.metadatacenter.util.GlobalContext import GlobalContext
from org.metadatacenter.util.Util import Util
from org.metadatacenter.worker.GitWorker import GitWorker

console = Console()

DSD_ORG = "dsd-sztaki-hu"
DSD_BASE = f"https://github.com/{DSD_ORG}/"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RATE_LIMIT_DELAY = 1.0  # seconds between API calls to avoid rate limiting


class ArpGitWorker:

    def __init__(self):
        self.git_worker = GitWorker()

    @staticmethod
    def _check_env_vars():
        if Const.CEDAR_VERSION not in os.environ:
            raise SystemExit(
                f"Error: {Const.CEDAR_VERSION} environment variable is not set."
            )
        if Const.ARP_BRANCH_SUFFIX not in os.environ:
            raise SystemExit(
                f"Error: {Const.ARP_BRANCH_SUFFIX} environment variable is not set."
            )

    def _fetch_dsd_branches(self, repo_name: str) -> Tuple[bool, List[str], int]:
        """
        Fetch branch names from dsd fork via GitHub API.
        Returns: (success, list of branch names, status_code). Empty list on failure or no branches.
        """
        url = f"{GITHUB_API_BASE}/repos/{DSD_ORG}/{repo_name}/branches"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if "GITHUB_TOKEN" in os.environ:
            headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 404:
                return False, [], 404
            if resp.status_code in (403, 429):
                return False, [], resp.status_code
            resp.raise_for_status()
            branches = [b["name"] for b in resp.json()]
            return True, branches, resp.status_code
        except requests.RequestException:
            return False, [], 0

    def _check_dsd_fork_branches(self, repo_name: str) -> Tuple[str, List[str], int]:
        """
        Check if dsd fork exists and what arp-* branches it has.
        Returns: (status, list of arp branch names, status_code)
        - status: "no_fork" | "has_branches" | "rate_limited"
        - status_code: HTTP status for rate limit detection (403, 429)
        """
        success, all_branches, status_code = self._fetch_dsd_branches(repo_name)
        if not success:
            if status_code in (403, 429):
                return "rate_limited", [], status_code
            return "no_fork", [], status_code

        arp_branches = [b for b in all_branches if b.startswith("arp-")]
        return "has_branches", arp_branches, status_code

    def _check_rate_limit(self) -> None:
        """Probe GitHub API and exit if rate limited."""
        success, _, status_code = self._fetch_dsd_branches("cedar-cli")
        if not success and status_code in (403, 429):
            console.print()
            console.print(Panel(
                "GitHub API rate limit exceeded (403/429).\n\n"
                "Set GITHUB_TOKEN for higher limits (5000/hour vs 60/hour):\n"
                "  export GITHUB_TOKEN=your_personal_access_token",
                title="[bold red]Rate Limit Error[/bold red]",
                style="red",
            ))
            raise SystemExit(1)

    def _run_fork_detect_and_checkout(
        self, cedar_version: str, arp_suffix: str, report_format: str = "override"
    ) -> None:
        """Run Phase 2 (fork detection), Phase 3 (checkout dsd), Phase 4 (report)."""
        expected_branch = f"arp-{cedar_version}{arp_suffix}"
        repo_list = GlobalContext.repos.get_list_top()
        has_fork_correct = []
        no_fork = []
        wrong_naming = []

        self._check_rate_limit()

        with Progress() as progress:
            task = progress.add_task("Checking forks...", total=len(repo_list))
            for repo in repo_list:
                status, arp_branches, status_code = self._check_dsd_fork_branches(repo.name)
                if status == "rate_limited":
                    console.print()
                    console.print(Panel(
                        "GitHub API rate limit exceeded (403/429).\n\n"
                        "Set GITHUB_TOKEN for higher limits (5000/hour vs 60/hour):\n"
                        "  export GITHUB_TOKEN=your_personal_access_token",
                        title="[bold red]Rate Limit Error[/bold red]",
                        style="red",
                    ))
                    raise SystemExit(1)
                if status == "no_fork":
                    no_fork.append(repo.name)
                elif expected_branch in arp_branches:
                    has_fork_correct.append(repo.name)
                elif arp_branches:
                    wrong_naming.append((repo.name, arp_branches, expected_branch))
                else:
                    no_fork.append(repo.name)
                progress.update(task, advance=1)
                if "GITHUB_TOKEN" not in os.environ:
                    time.sleep(GITHUB_RATE_LIMIT_DELAY)

        console.print()
        console.print("[bold]Phase 3: Checking out dsd branches...[/bold]")
        checked_out_ok = []
        checked_out_failed = []

        for repo_name in has_fork_correct:
            repo = GlobalContext.repos.map.get(repo_name)
            if not repo:
                continue
            cwd = Util.get_wd(repo)
            dsd_url = f"{DSD_BASE}{repo_name}.git"
            success = self._checkout_dsd_branch(cwd, expected_branch, dsd_url, repo_name)
            if success:
                checked_out_ok.append(repo_name)
            else:
                checked_out_failed.append(repo_name)

        self._print_report(
            expected_branch=expected_branch,
            has_fork_correct=has_fork_correct,
            no_fork=no_fork,
            wrong_naming=wrong_naming,
            checked_out_ok=checked_out_ok,
            checked_out_failed=checked_out_failed,
            report_format=report_format,
        )

    def override(self):
        self._check_env_vars()
        cedar_version = os.environ[Const.CEDAR_VERSION]
        arp_suffix = os.environ[Const.ARP_BRANCH_SUFFIX]
        expected_branch = f"arp-{cedar_version}{arp_suffix}"

        console.print(Panel(
            f"ARP Git Override\n"
            f"CEDAR_VERSION: {cedar_version}\n"
            f"ARP_BRANCH_SUFFIX: {arp_suffix}\n"
            f"Expected branch: {expected_branch}",
            title="Configuration",
            style=Style(color="blue"),
        ))

        console.print()
        console.print("[bold]Phase 2: Detecting dsd forks...[/bold]")
        self._run_fork_detect_and_checkout(cedar_version, arp_suffix)

    def upgrade(self, version: str = None):
        """
        Fetch, checkout release branch, then detect forks and checkout dsd branches.
        Does not clone repos - assumes they already exist.
        """
        self._check_env_vars()
        cedar_version = version or os.environ[Const.CEDAR_VERSION]
        arp_suffix = os.environ[Const.ARP_BRANCH_SUFFIX]
        expected_branch = f"arp-{cedar_version}{arp_suffix}"
        release_branch = f"release-{cedar_version}"

        console.print(Panel(
            f"ARP Git Upgrade\n"
            f"CEDAR_VERSION: {cedar_version}\n"
            f"ARP_BRANCH_SUFFIX: {arp_suffix}\n"
            f"Expected branch: {expected_branch}",
            title="Configuration",
            style=Style(color="blue"),
        ))

        console.print()
        console.print("[bold]Phase 1: Fetching all repos...[/bold]")
        self.git_worker.fetch()

        console.print()
        console.print(f"[bold]Phase 1: Checking out {release_branch}...[/bold]")
        self.git_worker.checkout(release_branch)

        console.print()
        console.print(f"[bold]Phase 1: Checking out cedar-cli to {expected_branch} (contains fork detection code)...[/bold]")
        cedar_cli_repo = GlobalContext.repos.map.get("cedar-cli")
        if cedar_cli_repo:
            cwd = Util.get_wd(cedar_cli_repo)
            dsd_url = f"{DSD_BASE}cedar-cli.git"
            self._checkout_dsd_branch(cwd, expected_branch, dsd_url, "cedar-cli")

        console.print()
        console.print("[bold]Phase 2: Detecting dsd forks...[/bold]")
        self._run_fork_detect_and_checkout(cedar_version, arp_suffix, report_format="upgrade")

    def _checkout_dsd_branch(
        self, cwd: str, branch_name: str, dsd_url: str, repo_name: str
    ) -> bool:
        """Checkout dsd branch in repo. Returns True on success."""
        try:
            result = subprocess.run(
                [
                    "bash", "-c",
                    f"git remote | grep -q dsd || git remote add dsd {dsd_url}; "
                    f"git fetch dsd; "
                    f"git checkout -B {branch_name} dsd/{branch_name} 2>/dev/null || "
                    f"git checkout {branch_name}; "
                    f"git pull"
                ],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                console.print(f"  [green]✓[/green] {repo_name}")
                return True
            else:
                console.print(f"  [red]✗[/red] {repo_name}: {result.stderr[:100]}")
                return False
        except Exception as e:
            console.print(f"  [red]✗[/red] {repo_name}: {e}")
            return False

    def _print_report(
        self,
        expected_branch: str,
        has_fork_correct: list,
        no_fork: list,
        wrong_naming: list,
        checked_out_ok: list,
        checked_out_failed: list,
        report_format: str = "override",
    ):
        console.print()
        console.print(Panel(
            "ARP Git - Results",
            title="Summary",
            style="bold cyan",
        ))
        console.print()

        if report_format == "upgrade":
            if checked_out_ok:
                console.print("[bold green]Checked out from dsd[/bold green]")
                for repo in sorted(checked_out_ok):
                    console.print("  " + repo)
                console.print()

            on_release = sorted(set(no_fork) | {r for r, _, _ in wrong_naming} | set(checked_out_failed))
            if on_release:
                console.print("[bold yellow]On release branch[/bold yellow]")
                for repo in on_release:
                    console.print("  " + repo)
        else:
            if has_fork_correct:
                console.print("[bold green]Has fork + correct branch ({})[/bold green]".format(expected_branch))
                for repo in sorted(has_fork_correct):
                    console.print("  " + repo)
                console.print()

            if no_fork:
                console.print("[bold yellow]No fork[/bold yellow]")
                for repo in sorted(no_fork):
                    console.print("  " + repo)
                console.print()

            if wrong_naming:
                console.print("[bold magenta]Fork but wrong naming[/bold magenta]")
                for repo_name, branches, expected in wrong_naming:
                    console.print("  {} (has: {}, expected: {})".format(
                        repo_name, ", ".join(branches), expected
                    ))
                console.print()

            if checked_out_ok:
                console.print("[bold green]Successfully checked out[/bold green]")
                for repo in sorted(checked_out_ok):
                    console.print("  " + repo)
                console.print()

            if checked_out_failed:
                console.print("[bold red]Checkout failed[/bold red]")
                for repo in sorted(checked_out_failed):
                    console.print("  " + repo)

        console.print()
        console.print(Panel(
            "If new cert generation is required, run:\n\n"
            "  rm -rf $CEDAR_HOME/CEDAR_CA\n"
            "  cedarcli cert setup\n"
            "  cedarcli cert ca\n"
            "  cedarcli cert domains\n"
            "  cedarcli docker one-time-setup",
            title="[dim]Optional: New cert setup[/dim]",
            style="dim",
        ))
