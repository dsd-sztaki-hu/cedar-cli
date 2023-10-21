from org.metadatacenter.model.PlanTask import PlanTask
from org.metadatacenter.model.PreReleaseBranchType import PreReleaseBranchType
from org.metadatacenter.model.ReleasePreparePhase import ReleasePreparePhase
from org.metadatacenter.model.Repo import Repo
from org.metadatacenter.model.RepoType import RepoType
from org.metadatacenter.model.TaskType import TaskType
from org.metadatacenter.util.GlobalContext import GlobalContext
from org.metadatacenter.util.Util import Util


class ReleasePrepareShellTaskFactory:

    def __init__(self):
        super().__init__()

    @classmethod
    def prepare_java(cls, repo: Repo, branch_type: PreReleaseBranchType, release_prepare_phase: ReleasePreparePhase) -> PlanTask:
        from org.metadatacenter.util.GlobalContext import GlobalContext
        task = PlanTask(cls.get_typed_name("java wrapper/java", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        allow_snapshots = Util.get_allow_snapshots(branch_type)
        allow_snapshots_flag = '-DallowSnapshots=' + ('true' if allow_snapshots else 'false')
        replace_version_commands = []
        build_command = ''

        if repo in GlobalContext.repos.get_parent():
            build_command = '      mvn clean install -DskipTests'
        elif repo.repo_type == RepoType.JAVA_WRAPPER or repo.repo_type == RepoType.JAVA:
            build_command = '      mvn clean install -DskipTests'

        if release_prepare_phase == ReleasePreparePhase.SET_VERSIONS:
            if repo in GlobalContext.repos.get_parent():
                replace_version_commands = [
                    "      xmlstarlet ed -L -u '_:project/_:version' -v '" + version + "' pom.xml",
                    "      xmlstarlet ed -L -u '_:project/_:properties/_:cedar.version' -v '" + version + "' pom.xml"]
            elif repo.repo_type == RepoType.JAVA_WRAPPER or repo.repo_type == RepoType.JAVA:
                replace_version_commands = [
                    '      mvn versions:set -DnewVersion="' + version + '" -DupdateMatchingVersions=false',
                    '      mvn versions:update-parent versions:update-child-modules ' + allow_snapshots_flag,
                    '      mvn versions:update-properties ' + allow_snapshots_flag]

            task.command_list.extend([
                'echo "Update to next release version"',
                *replace_version_commands,
            ])
            # Special case for parent, needs to be built for the versions plugin to work correctly
            if repo in GlobalContext.repos.get_parent():
                task.command_list.extend([
                    'echo "Build release version"',
                    build_command,
                ])
            return task

        elif release_prepare_phase == ReleasePreparePhase.BUILD:
            task.command_list.extend([
                'echo "Build release version"',
                build_command,
                *cls.macro_commit_changes(branch_name),
                *(cls.macro_tag_repo(tag_name) if tag_name is not None else [])
            ])
            return task

    @classmethod
    def prepare_angular_js(cls, repo: Repo, branch_type: PreReleaseBranchType,
                           release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("angularJS project", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
            *cls.macro_update_package_json_and_travis(version),
            *cls.macro_build_angular_js(),
            *cls.macro_commit_changes(branch_name),
            *(cls.macro_tag_repo(tag_name) if tag_name is not None else [])
        ])
        return task

    @classmethod
    def prepare_angular_src(cls, repo: Repo, branch_type: PreReleaseBranchType,
                            release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("angular standalone project", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
            *cls.macro_update_package_json_and_travis(version),
            *cls.macro_update_index_html_version_numbers(version),
            *cls.macro_build_angular(),
            *cls.macro_commit_changes(branch_name),
            *(cls.macro_tag_repo(tag_name) if tag_name is not None else [])
        ])
        return task

    @classmethod
    def prepare_angular_dist(cls, repo: Repo, branch_type: PreReleaseBranchType,
                             release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("angular dist standalone project", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
            *cls.macro_update_package_json_and_travis(version),
            *cls.macro_build_angular(),
            *cls.macro_commit_changes(branch_name),
            *(cls.macro_tag_repo(tag_name) if tag_name is not None else [])
        ])
        return task

    @classmethod
    def prepare_angular_src_sub(cls, repo: Repo, branch_type: PreReleaseBranchType,
                                release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("angular sub-project", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
            *cls.macro_update_package_json_and_travis(version),
            *cls.macro_update_index_html_version_numbers(version),
            *cls.macro_build_angular(),
        ])
        return task

    @classmethod
    def prepare_angular_dist_sub(cls, repo: Repo, branch_type: PreReleaseBranchType,
                                 release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("angular dist sub-project", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
            *cls.macro_update_package_json_and_travis(version),
        ])
        return task

    @classmethod
    def prepare_plain_sub(cls, repo: Repo, branch_type: PreReleaseBranchType,
                          release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("plain sub repo", branch_type), TaskType.SHELL, repo)
        task.command_list = [
        ]
        return task

    @classmethod
    def prepare_multi_pre(cls, repo: Repo, branch_type: PreReleaseBranchType,
                          release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("PRE multi directory project", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
        ])
        return task

    @classmethod
    def prepare_multi_post(cls, repo: Repo, branch_type: PreReleaseBranchType,
                           release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("POST multi directory project", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
            *cls.macro_commit_changes(branch_name),
            *(cls.macro_tag_repo(tag_name) if tag_name is not None else [])
        ])
        return task

    @classmethod
    def prepare_plain(cls, repo: Repo, branch_type: PreReleaseBranchType,
                      release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("plain repo", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
            *cls.macro_commit_changes(branch_name),
            *(cls.macro_tag_repo(tag_name) if tag_name is not None else [])
        ])
        return task

    @classmethod
    def prepare_development(cls, repo: Repo, branch_type: PreReleaseBranchType,
                            release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("development repo", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
            *cls.macro_update_development_cedar_version(version),
            *cls.macro_commit_changes(branch_name),
            *(cls.macro_tag_repo(tag_name) if tag_name is not None else [])
        ])
        return task

    @classmethod
    def prepare_docker_deploy(cls, repo: Repo, branch_type: PreReleaseBranchType,
                              release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("Docker deploy repo", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
            *cls.macro_update_env_cedar_docker_version(version),
            *cls.macro_commit_changes(branch_name),
            *(cls.macro_tag_repo(tag_name) if tag_name is not None else [])
        ])
        return task

    @classmethod
    def prepare_docker_build(cls, repo: Repo, branch_type: PreReleaseBranchType,
                             release_prepare_phase: ReleasePreparePhase) -> PlanTask or None:
        if release_prepare_phase == ReleasePreparePhase.BUILD:
            return
        task = PlanTask(cls.get_typed_name("Docker build repo", branch_type), TaskType.SHELL, repo)
        task.command_list = []
        version, branch_name, tag_name = Util.get_release_vars(branch_type)
        task.command_list.extend([
            *cls.macro_update_docker_build_versions(version),
            *cls.macro_commit_changes(branch_name),
            *(cls.macro_tag_repo(tag_name) if tag_name is not None else [])
        ])
        return task

    @classmethod
    def macro_tag_repo(cls, tag_name: str):
        return ('echo "Tag repo with version"',
                '      git tag "' + tag_name + '"',
                '      git push origin "' + tag_name + '"')

    @classmethod
    def macro_commit_changes(cls, branch_name: str):
        return ('echo "Commit changes after build"',
                '      git add .',
                '      git commit -a -m "Produce version of component" --allow-empty')

    @classmethod
    def macro_update_index_html_version_numbers(cls, version: str):
        return ('echo "Update openview and bridging index.html"',
                "      if [[ -e src/index.html ]]; then " + GlobalContext.get_sed_replace_in_place() + " 's/\/cedar-artifact-viewer-.*\.js/\/cedar-artifact-viewer-'" + version + "'\.js/g' src/index.html; fi",
                "      if [[ -e src/index.html ]]; then " + GlobalContext.get_sed_replace_in_place() + " 's/\/cedar-embeddable-editor-.*\.js/\/cedar-embeddable-editor-'" + version + "'\.js/g' src/index.html; fi")

    @classmethod
    def macro_update_package_json_and_travis(cls, version: str):
        return ('echo "Update to next release version"',
                "      jq '.version=\"'" + version + "'\"' package.json | sponge package.json",
                "      jq '.version=\"'" + version + "'\"' package-lock.json | sponge package-lock.json",
                "      jq '.packages[\"\"].version=\"'" + version + "'\"' package-lock.json | sponge package-lock.json",
                "      if [[ -e .travis.yml ]]; then " + GlobalContext.get_sed_replace_in_place() + " 's/- CEDAR_VERSION\s*=.*\".*\"/- CEDAR_VERSION=\"'" + version + "'\"/g' .travis.yml; fi")

    @classmethod
    def macro_update_development_cedar_version(cls, version: str):
        return ('echo "Update to next release version"',
                "      " + GlobalContext.get_sed_replace_in_place() + " 's/^export CEDAR_VERSION=.*$/export CEDAR_VERSION='" + version + "'/' ./bin/util/set-env-generic.sh")

    @classmethod
    def macro_update_env_cedar_docker_version(cls, version: str):
        return ('echo "Update to next release version"',
                "      find . -name .env -exec " + GlobalContext.get_sed_replace_in_place() + " 's/^CEDAR_DOCKER_VERSION=.*$/CEDAR_DOCKER_VERSION='" + version + "'/' {} \; -print")

    @classmethod
    def macro_update_docker_build_versions(cls, version: str):
        return ('echo "Update to next release version"',
                "      find . -name Dockerfile -exec " + GlobalContext.get_sed_replace_in_place() + " 's/^FROM metadatacenter\/cedar-microservice:.*$/FROM metadatacenter\/cedar-microservice:'" + version + "'/' {} \; -print",
                "      find . -name Dockerfile -exec " + GlobalContext.get_sed_replace_in_place() + " 's/^FROM metadatacenter\/cedar-java:.*$/FROM metadatacenter\/cedar-java:'" + version + "'/' {} \; -print",
                "      find . -name Dockerfile -exec " + GlobalContext.get_sed_replace_in_place() + " 's/^ENV CEDAR_VERSION=.*$/ENV CEDAR_VERSION='" + version + "'/' {} \; -print",
                "      " + GlobalContext.get_sed_replace_in_place() + " 's/^export IMAGE_VERSION=.*$/export IMAGE_VERSION='" + version + "'/' ./bin/cedar-images-base.sh"
                )

    @classmethod
    def macro_build_angular(cls):
        return ('echo "Build release version"',
                '      npm install --legacy-peer-deps',
                '      ng build --configuration=production')

    @classmethod
    def macro_build_angular_js(cls):
        return ('echo "Build release version"',
                '      npm install')

    @classmethod
    def get_typed_name(cls, name, branch_type: PreReleaseBranchType):
        s = "Prepare " + name + " for "
        s += " pre-release" if branch_type == PreReleaseBranchType.RELEASE else "next dev"
        return s
