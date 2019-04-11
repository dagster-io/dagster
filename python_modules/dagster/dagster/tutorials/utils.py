import subprocess


def check_script(path):
    subprocess.check_output(['python', path])


def check_cli_execute_file_pipeline(path, pipeline_fn_name, env_file=None):
    cli_cmd = ['python', '-m', 'dagster', 'pipeline', 'execute', '-f', path, '-n', pipeline_fn_name]

    if env_file:
        cli_cmd.append('-e')
        cli_cmd.append(env_file)

    try:
        subprocess.check_output(cli_cmd)
    except subprocess.CalledProcessError as cpe:
        print(cpe)
        raise cpe
