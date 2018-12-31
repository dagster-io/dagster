import subprocess


def check_script(path):
    subprocess.check_output(['python', path])


def check_cli_execute_file_pipeline(path, pipeline_fn_name):
    cli_cmd = [
        'python',
        '-m',
        'dagster',
        'pipeline',
        'execute',
        '-f',
        path,
        '-n',
        pipeline_fn_name,
    ]

    subprocess.check_output(cli_cmd)
