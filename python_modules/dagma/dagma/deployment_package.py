# """Utilities to construct and upload the deployment package used by our Lambda handler."""

# import logging
# import os
# import subprocess
# import tempfile

# from .utils import zip_folder
# from .version import __version__

# DAGMA_RUNTIME_BUCKET = 'dagma-runtime'

# PYTHON_DEPENDENCIES = [
#     'boto3', 'cloudpickler', 'git+ssh://git@github.com/dagster-io/dagster.git'
#     '@lambda_engine#egg=dagma&subdirectory=python_modules/dagma'
# ]

# logger = logging.getLogger(__name__)

# # # FIXME only do this *once* -- actually, this can live in a publicly accessible S3 bucket of its
# # # own
# def _construct_deployment_package(logger=logger):
#     deployment_package_dir = tempfile.mkdtemp()
#     TEMPDIR_REGISTRY.append(deployment_package_dir)

#     for python_dependency in python_dependencies:
#         process = subprocess.Popen(
#             ['pip', 'install', python_dependency, '--target', deployment_package_dir],
#             stderr=subprocess.PIPE,
#             stdout=subprocess.PIPE
#         )
#         for line in iter(process.stdout.readline, b''):
#             context.debug(line.decode('utf-8'))

#     archive_dir = tempfile.mkdtemp()
#     TEMPDIR_REGISTRY.append(archive_dir)
#     archive_path = os.path.join(tempfile.mkdtemp(), get_deployment_package_key(context, step_idx))

#     try:
#         pwd = os.getcwd()
#         os.chdir(deployment_package_dir)
#         zip_folder('.', archive_path)
#         context.debug(
#             'Zipped archive at {archive_path}: {size} bytes'.format(
#                 archive_path=archive_path, size=os.path.getsize(archive_path)
#             )
#         )
#     finally:
#         os.chdir(pwd)

#     try:
#         yield archive_path
#     finally:
#         pass
#         # Cleanup tempdir
