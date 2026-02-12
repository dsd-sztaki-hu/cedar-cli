import typer

from org.metadatacenter.worker.ArpGitWorker import ArpGitWorker

app = typer.Typer(no_args_is_help=True)

arp_git_app = typer.Typer(no_args_is_help=True)
app.add_typer(arp_git_app, name="git", help="ARP git operations on dsd forks")

arp_git_worker = ArpGitWorker()


@arp_git_app.command("override", help="Clone all, checkout release branch, then override with dsd arp branches where available")
def override():
    arp_git_worker.override()


@arp_git_app.command("upgrade", help="Fetch, checkout release branch, detect forks and checkout dsd branches (no clone)")
def upgrade(version: str = typer.Argument(None, help="CEDAR version (default: $CEDAR_VERSION)")):
    arp_git_worker.upgrade(version)
