from subprocess import check_output


def get_root_git_dir():
    return check_output(['git', 'rev-parse', '--show-toplevel']).decode().rstrip()
