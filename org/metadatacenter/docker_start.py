import typer

from org.metadatacenter.worker.DockerWorker import DockerWorker

app = typer.Typer(no_args_is_help=True)


@app.command("infrastructure")
def start_infrastructure():
    DockerWorker.start_infrastructure()


@app.command("infrastructureext")
def start_infrastructure_ext():
    DockerWorker.start_infrastructure_ext()


@app.command("microservices")
def start_microservices():
    DockerWorker.start_microservices()


@app.command("microservicesext")
def start_microservices_ext():
    DockerWorker.start_microservices_ext()


@app.command("frontends")
def start_frontends():
    DockerWorker.start_frontends()


@app.command("frontendsext")
def start_frontends_ext():
    DockerWorker.start_frontends_ext()
