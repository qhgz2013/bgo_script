__all__ = ['VERSION']


def version_wrapper() -> str:
    from util import spawn_process
    git_tag = spawn_process('git tag --points-at HEAD')
    if len(git_tag) > 0:
        return git_tag
    else:
        git_branch = spawn_process('git rev-parse --abbrev-ref HEAD')
        git_hash = spawn_process('git rev-parse --short HEAD')
        git_time = spawn_process('git show -s --format=%cI HEAD')
        return f'{git_branch}-{git_hash}-{git_time}'


try:
    VERSION = version_wrapper()
except Exception as ex:
    from warnings import warn
    warn(str(ex))
    VERSION = 'unknown'
