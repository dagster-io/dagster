"""Utilities to construct and upload the deployment package used by our Lambda handler."""

import contextlib

# https://github.com/PyCQA/pylint/issues/73
import distutils.spawn  # pylint: disable=no-name-in-module, import-error
import os
import subprocess

from botocore.exceptions import ClientError

from dagster.utils.zip import zip_folder

from .config import PYTHON_DEPENDENCIES
from .utils import tempdirs
from .version import __version__


def _which(exe):
    # https://github.com/PyCQA/pylint/issues/73
    return distutils.spawn.find_executable(exe)  # pylint: disable=no-member


def _get_deployment_package_key():
    return 'dagma_runtime_{version}'.format(version=__version__)


@contextlib.contextmanager
def _construct_deployment_package(context, key):

    if _which('pip') is None:
        raise Exception('Couldn\'t find \'pip\' -- can\'t construct a deployment package')

    if _which('git') is None:
        raise Exception('Couldn\'t find \'git\' -- can\'t construct a deployment package')

    with tempdirs(2) as (deployment_package_dir, archive_dir):
        for python_dependency in PYTHON_DEPENDENCIES:
            process = subprocess.Popen(
                ['pip', 'install', python_dependency, '--target', deployment_package_dir],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            for line in iter(process.stdout.readline, b''):
                context.debug(line.decode('utf-8'))

        archive_path = os.path.join(archive_dir, key)

        try:
            pwd = os.getcwd()
            os.chdir(deployment_package_dir)
            zip_folder('.', archive_path)
            context.debug(
                'Zipped archive at {archive_path}: {size} bytes'.format(
                    archive_path=archive_path, size=os.path.getsize(archive_path)
                )
            )
        finally:
            os.chdir(pwd)

        yield archive_path


def _upload_deployment_package(context, key, path):
    context.debug('Uploading deployment package')
    with open(path, 'rb') as fd:
        return context.resources.dagma.storage.client.put_object(
            Bucket=context.resources.dagma.runtime_bucket, Key=key, Body=fd
        )
    context.debug('Done uploading deployment package')


def _create_and_upload_deployment_package(context, key):
    with _construct_deployment_package(context, key) as deployment_package_path:
        _upload_deployment_package(context, key, deployment_package_path)


def _get_deployment_package(context, key):
    try:
        context.resources.dagma.storage.client.head_object(
            Bucket=context.resources.dagma.runtime_bucket, Key=key
        )
        return key
    except ClientError:
        return None


def get_or_create_deployment_package(context):
    deployment_package_key = _get_deployment_package_key()

    context.debug(
        'Looking for deployment package at {s3_bucket}/{s3_key}'.format(
            s3_bucket=context.resources.dagma.runtime_bucket, s3_key=deployment_package_key
        )
    )

    if _get_deployment_package(context, deployment_package_key):
        context.debug('Found deployment package!')
        return deployment_package_key

    context.debug('Creating deployment package...')
    _create_and_upload_deployment_package(context, deployment_package_key)

    return deployment_package_key
