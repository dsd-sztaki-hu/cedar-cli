import base64
import os
import tempfile
from urllib.parse import urlparse
from org.metadatacenter.model.PlanTask import PlanTask
from org.metadatacenter.model.Repo import Repo
from org.metadatacenter.model.TaskType import TaskType
from org.metadatacenter.util.Util import Util

# Stanford Nexus uses /repository/snapshots and /repository/releases
# DSD Nexus uses /repository/maven-snapshots and /repository/maven-releases
_DEFAULT_MAVEN_SNAPSHOTS_URL = 'https://nexus.bmir.stanford.edu/repository/snapshots'
_DEFAULT_MAVEN_RELEASES_URL = 'https://nexus.bmir.stanford.edu/repository/releases'


class DeployShellTaskFactory:

    def __init__(self):
        super().__init__()

    @classmethod
    def _get_maven_settings_path(cls) -> str:
        """Get settings path for Maven. settings.xml uses ${env.CEDAR_MAVEN_SNAPSHOTS_URL}
        and ${env.CEDAR_MAVEN_RELEASES_URL} for repository URLs."""
        os.environ.setdefault('CEDAR_MAVEN_SNAPSHOTS_URL', _DEFAULT_MAVEN_SNAPSHOTS_URL)
        os.environ.setdefault('CEDAR_MAVEN_RELEASES_URL', _DEFAULT_MAVEN_RELEASES_URL)

        settings_path = os.environ.get('CEDAR_MAVEN_SETTINGS')
        if settings_path and os.path.isfile(settings_path):
            return settings_path
        default_path = os.path.join(
            Util.cedar_home,
            'cedar-docker-build/cedar-microservice/config/m2/settings.xml'
        )
        return default_path if os.path.isfile(default_path) else ''

    @classmethod
    def _get_npm_auth_args(cls, registry: str) -> str:
        """When CEDAR_NEXUS_USERNAME/PASSWORD are set, create temp .npmrc with auth
        and return --userconfig=PATH for npm publish."""
        username = os.environ.get('CEDAR_NEXUS_USERNAME')
        password = os.environ.get('CEDAR_NEXUS_PASSWORD')
        if not username or not password:
            return ''

        parsed = urlparse(registry)
        auth_key = f"//{parsed.netloc}{parsed.path.rstrip('/')}/"
        auth_value = base64.b64encode(f"{username}:{password}".encode()).decode()

        content = f"{auth_key}:_auth={auth_value}\n{auth_key}:always-auth=true\n"
        fd, tmp_path = tempfile.mkstemp(suffix='.npmrc', prefix='cedar-npm-')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            return f' --userconfig={tmp_path}'
        except Exception:
            os.unlink(tmp_path)
            raise

    @classmethod
    def maven_deploy_skip_tests(cls, repo: Repo) -> PlanTask:
        task = PlanTask("Maven deploy skip tests", TaskType.SHELL, repo)

        # Support custom Maven repository URLs
        maven_cmd = 'mvn deploy -DskipTests'

        settings_path = cls._get_maven_settings_path()
        if settings_path:
            maven_cmd += f' -s {settings_path}'

        # Add custom repository URLs if specified (for deployment target)
        snapshots_url = os.environ.get('CEDAR_MAVEN_SNAPSHOTS_URL')
        releases_url = os.environ.get('CEDAR_MAVEN_RELEASES_URL')

        if snapshots_url and releases_url:
            maven_cmd += f' -Dnexus.snapshots.url={snapshots_url}'
            maven_cmd += f' -Dnexus.releases.url={releases_url}'

        task.command_list = [maven_cmd]
        return task

    @classmethod
    def npm_publish(cls, repo: Repo) -> PlanTask:
        task = PlanTask("NPM publish", TaskType.SHELL, repo)

        # Support custom npm registry with optional auth from env vars
        registry = os.environ.get('CEDAR_NPM_REGISTRY')
        if registry:
            auth_args = cls._get_npm_auth_args(registry)
            task.command_list = [f'npm publish --registry={registry}{auth_args}']
        else:
            task.command_list = ['npm publish']

        return task

    @classmethod
    def npm_install_publish(cls, repo: Repo) -> PlanTask:
        task = PlanTask("NPM install, NPM publish", TaskType.SHELL, repo)

        # Support custom npm registry with optional auth from env vars
        registry = os.environ.get('CEDAR_NPM_REGISTRY')
        if registry:
            auth_args = cls._get_npm_auth_args(registry)
            task.command_list = [
                'npm install',
                f'npm publish --registry={registry}{auth_args}'
            ]
        else:
            task.command_list = ['npm install', 'npm publish']

        return task