from rich.console import Console

from org.metadatacenter.model.PlanTask import PlanTask
from org.metadatacenter.model.PrePostType import PrePostType
from org.metadatacenter.model.PreReleaseBranchType import PreReleaseBranchType
from org.metadatacenter.model.ReleasePreparePhase import ReleasePreparePhase
from org.metadatacenter.model.RepoRelationType import RepoRelationType
from org.metadatacenter.model.RepoType import RepoType
from org.metadatacenter.model.TaskType import TaskType
from org.metadatacenter.operator.BuildOperator import BuildOperator
from org.metadatacenter.operator.Operator import Operator
from org.metadatacenter.taskfactory.BuildShellTaskFactory import BuildShellTaskFactory
from org.metadatacenter.taskfactory.ReleasePrepareShellTaskFactory import ReleasePrepareShellTaskFactory
from org.metadatacenter.util.GlobalContext import GlobalContext

console = Console()


class ReleasePrepareOperator(Operator):

    def __init__(self):
        super().__init__()

    @staticmethod
    def expand(task: PlanTask):
        ReleasePrepareOperator.expand_for_release(task, task.parameters['branch_type'], task.parameters['release_prepare_phase'])

    @classmethod
    def expand_for_release(cls, task, branch_type: PreReleaseBranchType, release_prepare_phase: ReleasePreparePhase):

        repo_list = [task.repo]

        for repo in repo_list:
            if repo.repo_type == RepoType.JAVA_WRAPPER:
                shell_wrapper = PlanTask("Prepare release of java wrapper project", TaskType.SHELL_WRAPPER, repo)
                shell_wrapper.add_task_as_task(ReleasePrepareShellTaskFactory.prepare_java(repo, branch_type, release_prepare_phase))
                task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.JAVA:
                shell_wrapper = PlanTask("Prepare release of java project", TaskType.SHELL_WRAPPER, repo)
                shell_wrapper.add_task_as_task(ReleasePrepareShellTaskFactory.prepare_java(repo, branch_type, release_prepare_phase))
                task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.ANGULAR:
                if repo.pre_post_type == PrePostType.SUB:
                    shell_wrapper = PlanTask("Prepare release of angular sub-project", TaskType.SHELL_WRAPPER, repo)
                    shell_wrapper.add_task_as_task(
                        ReleasePrepareShellTaskFactory.prepare_angular_src_sub(repo, branch_type, release_prepare_phase))
                    task.add_task_as_task(shell_wrapper)
                elif repo.pre_post_type == PrePostType.NONE:
                    shell_wrapper = PlanTask("Prepare release of angular standalone project", TaskType.SHELL_WRAPPER, repo)
                    shell_wrapper.add_task_as_task(
                        ReleasePrepareShellTaskFactory.prepare_angular_src(repo, branch_type, release_prepare_phase))
                    task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.ANGULAR_DIST:
                if repo.pre_post_type == PrePostType.SUB:
                    shell_wrapper = PlanTask("Prepare release of angular dist sub-project", TaskType.SHELL_WRAPPER, repo)
                    shell_wrapper.add_task_as_task(
                        ReleasePrepareShellTaskFactory.prepare_angular_dist_sub(repo, branch_type, release_prepare_phase))
                    task.add_task_as_task(shell_wrapper)
                elif repo.pre_post_type == PrePostType.NONE:
                    shell_wrapper = PlanTask("Prepare release of angular dist standalone project", TaskType.SHELL_WRAPPER, repo)
                    shell_wrapper.add_task_as_task(
                        ReleasePrepareShellTaskFactory.prepare_angular_dist(repo, branch_type, release_prepare_phase))
                    task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.ANGULAR_JS:
                shell_wrapper = PlanTask("Prepare release of angularJS project", TaskType.SHELL_WRAPPER, repo)
                shell_wrapper.add_task_as_task(ReleasePrepareShellTaskFactory.prepare_angular_js(repo, branch_type, release_prepare_phase))
                task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.MULTI:
                if repo.pre_post_type == PrePostType.PRE:
                    shell_wrapper = PlanTask("Prepare release multi project", TaskType.SHELL_WRAPPER, repo)
                    shell_wrapper.add_task_as_task(
                        ReleasePrepareShellTaskFactory.prepare_multi_pre(repo, branch_type, release_prepare_phase))
                    task.add_task_as_task(shell_wrapper)
                elif repo.pre_post_type == PrePostType.POST:
                    shell_wrapper = PlanTask("Wrap up release multi project", TaskType.SHELL_WRAPPER, repo)
                    shell_wrapper.add_task_as_task(
                        ReleasePrepareShellTaskFactory.prepare_multi_post(repo, branch_type, release_prepare_phase))
                    task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.MKDOCS:
                shell_wrapper = PlanTask("Prepare release of mkdocs repo", TaskType.SHELL_WRAPPER, repo)
                shell_wrapper.add_task_as_task(ReleasePrepareShellTaskFactory.prepare_plain(repo, branch_type, release_prepare_phase))
                task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.CONTENT_DELIVERY:
                shell_wrapper = PlanTask("Prepare release of content delivery repo", TaskType.SHELL_WRAPPER, repo)
                shell_wrapper.add_task_as_task(ReleasePrepareShellTaskFactory.prepare_plain(repo, branch_type, release_prepare_phase))
                task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.MISC:
                shell_wrapper = PlanTask("Prepare release of miscellaneous repo", TaskType.SHELL_WRAPPER, repo)
                shell_wrapper.add_task_as_task(ReleasePrepareShellTaskFactory.prepare_plain(repo, branch_type, release_prepare_phase))
                task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.PYTHON:
                shell_wrapper = PlanTask("Prepare release of python repo", TaskType.SHELL_WRAPPER, repo)
                shell_wrapper.add_task_as_task(ReleasePrepareShellTaskFactory.prepare_plain(repo, branch_type, release_prepare_phase))
                task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.PHP:
                if repo.pre_post_type == PrePostType.SUB:
                    shell_wrapper = PlanTask("Prepare release of PHP sub-project", TaskType.SHELL_WRAPPER, repo)
                    shell_wrapper.add_task_as_task(
                        ReleasePrepareShellTaskFactory.prepare_plain_sub(repo, branch_type, release_prepare_phase))
                    task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.DEVELOPMENT:
                shell_wrapper = PlanTask("Prepare release of development repo", TaskType.SHELL_WRAPPER, repo)
                shell_wrapper.add_task_as_task(ReleasePrepareShellTaskFactory.prepare_development(repo, branch_type, release_prepare_phase))
                task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.DOCKER_DEPLOY:
                shell_wrapper = PlanTask("Prepare release of Docker deploy repo", TaskType.SHELL_WRAPPER, repo)
                shell_wrapper.add_task_as_task(
                    ReleasePrepareShellTaskFactory.prepare_docker_deploy(repo, branch_type, release_prepare_phase))
                task.add_task_as_task(shell_wrapper)
            elif repo.repo_type == RepoType.DOCKER_BUILD:
                shell_wrapper = PlanTask("Prepare release of Docker build repo", TaskType.SHELL_WRAPPER, repo)
                shell_wrapper.add_task_as_task(
                    ReleasePrepareShellTaskFactory.prepare_docker_build(repo, branch_type, release_prepare_phase))
                task.add_task_as_task(shell_wrapper)
            else:
                not_handled = PlanTask("Skip repo", TaskType.NOOP, repo)
                not_handled.add_task_as_task(BuildShellTaskFactory.noop(repo))
                task.add_task_as_task(not_handled)

            source_of_relations = GlobalContext.repos.get_relations(repo, RepoRelationType.IS_SOURCE_OF)
            for source_of_relation in source_of_relations:
                BuildOperator.handle_is_source_of(source_of_relation, task)
