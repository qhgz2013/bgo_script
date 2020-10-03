__all__ = ['VERSION']


def version_wrapper() -> str:
    from util import spawn_process
    git_tag = spawn_process('git tag --points-at HEAD')[1]
    worktree_flag = spawn_process('git diff-index --quiet HEAD')[0]
    worktree_status = '-dirty' if worktree_flag != 0 else ''
    if len(git_tag) > 0:
        return git_tag + worktree_status
    else:
        git_branch = spawn_process('git rev-parse --abbrev-ref HEAD')[1]
        git_hash = spawn_process('git rev-parse --short HEAD')[1]
        git_time = spawn_process('git show -s --format=%cI HEAD')[1]
        return f'{git_branch}-{git_hash}-{git_time}{worktree_status}'


try:
    VERSION = version_wrapper()
except Exception as ex:
    from warnings import warn
    warn(str(ex))
    VERSION = 'unknown'
