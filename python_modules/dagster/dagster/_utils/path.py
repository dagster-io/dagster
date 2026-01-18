import os


def is_likely_venv_executable(executable_path: str) -> bool:
    # venvs have a file called activate in the same bin directory as the Python executable
    return os.path.exists(os.path.join(os.path.dirname(executable_path), "activate"))
