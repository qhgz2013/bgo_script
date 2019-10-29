__all__ = ['VERSION']


def version_wrapper() -> str:
    import locale
    encoding = locale.getpreferredencoding()

    def spawn_process(cmd: str) -> str:
        import subprocess
        git_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        git_proc.wait()
        err_msg = git_proc.stderr.read()
        out_msg = git_proc.stdout.read()
        if len(err_msg) > 0:
            raise RuntimeError(str(err_msg, encoding).rstrip('\n'))
        return str(out_msg, encoding).rstrip('\n')
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
