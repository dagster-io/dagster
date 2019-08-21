# -*- coding: utf-8 -*-

import os
import signal
import subprocess
import sys

import boto3
import click

from dagster import DagsterInvariantViolationError
from dagster.utils import dagster_home_dir

from .aws_util import (
    create_ec2_instance,
    create_key_pair,
    get_or_create_security_group,
    get_validated_ami_id,
    select_region,
    select_vpc,
)
from .config import HostConfig
from .term import Term


def get_dagster_home():
    '''Ensures that the user has set a valid DAGSTER_HOME in environment and that it exists
    '''
    try:
        dagster_home = dagster_home_dir()
    except DagsterInvariantViolationError:
        Term.fatal(
            '''DAGSTER_HOME is not set! Before continuing, set with e.g.:

export DAGSTER_HOME=~/.dagster

You may want to add this line to your .bashrc or .zshrc file.
'''
        )

    Term.info('Found DAGSTER_HOME in environment at: %s\n' % dagster_home)

    if not os.path.isdir(dagster_home):
        Term.fatal('The specified DAGSTER_HOME folder does not exist! Create before continuing.')
    return dagster_home


def exit_gracefully(_signum, _frame):
    '''Prevent stack trace spew on Ctrl-C
    '''
    click.echo(click.style('\n\nCommand killed by keyboard interrupt, quitting\n\n', fg='yellow'))
    sys.exit(1)


@click.group()
def main():
    signal.signal(signal.SIGINT, exit_gracefully)


@main.command()
def init():
    click.echo('\n🌈 Welcome to Dagit + AWS quickstart cloud init!\n')

    # this ensures DAGSTER_HOME exists before we continue
    dagster_home = get_dagster_home()

    already_run = HostConfig.exists(dagster_home)
    if already_run:
        click.confirm(
            'dagster-aws has already been initialized! Continue?', default=False, abort=True
        )

    region = select_region()

    client = boto3.client('ec2', region_name=region)
    ec2 = boto3.resource('ec2', region_name=region)

    vpc = select_vpc(client, ec2)

    security_group_id = get_or_create_security_group(client, ec2, vpc)

    ami_id = get_validated_ami_id(client)

    key_pair_name, key_file_path = create_key_pair(client, dagster_home)

    inst = create_ec2_instance(ec2, security_group_id, ami_id, key_pair_name)

    # Save host configuration for future commands
    cfg = HostConfig(
        inst.public_dns_name, region, security_group_id, key_pair_name, key_file_path, ami_id
    )
    cfg.save(dagster_home)

    click.echo(
        click.style(
            '''🚀 To sync your Dagster project, in your project directory, run:

    dagster-aws up

You can also open a shell on your dagster-aws instance with:

    dagster-aws shell

For full details, see dagster-aws --help
            ''',
            fg='green',
        )
    )


@main.command()
def shell():
    dagster_home = get_dagster_home()
    cfg = HostConfig.load(dagster_home)

    ssh_cmd = 'ssh -i %s ubuntu@%s' % (cfg.key_file_path, cfg.public_dns_name)
    Term.waiting('Connecting to host...\n%s' % ssh_cmd)
    subprocess.call(ssh_cmd, shell=True)


@main.command()
def up():
    dagster_home = get_dagster_home()
    cfg = HostConfig.load(dagster_home)

    if cfg.local_path is None:
        cwd = os.getcwd()
        Term.info('Local path not configured; setting to %s' % cwd)
        cfg = cfg._replace(local_path=cwd)
        cfg.save(dagster_home)

    if not os.path.exists(os.path.join(cfg.local_path, 'repository.yaml')):
        Term.fatal('No repository.yaml found in %s, create before continuing.' % cfg.local_path)

    rsync_command = [
        'rsync',
        '-avL',
        '--progress',
        # Exclude a few common paths
        '--exclude',
        '\'.pytest_cache\'',
        '--exclude',
        '\'.git\'',
        '--exclude',
        '\'__pycache__\'',
        '--exclude',
        '\'*.pyc\'',
        '-e',
        '"ssh -i %s"' % cfg.key_file_path,
        '%s/*' % cfg.local_path,
        'ubuntu@%s:/opt/dagster/app' % cfg.public_dns_name,
    ]
    Term.info('rsyncing local path %s to %s' % (cfg.local_path, cfg.public_dns_name))
    click.echo('\n' + ' '.join(rsync_command) + '\n')
    subprocess.call(' '.join(rsync_command), shell=True)

    ssh_command = [
        'ssh',
        '-i',
        cfg.key_file_path,
        '-t',
        'ubuntu@%s' % cfg.public_dns_name,
        '\"sudo systemctl restart dagit\"',
    ]
    subprocess.call(' '.join(ssh_command), shell=True)
