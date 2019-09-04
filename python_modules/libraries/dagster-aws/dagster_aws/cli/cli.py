# -*- coding: utf-8 -*-

import os
import signal
import subprocess
import sys
import time
import webbrowser

import boto3
import click

from .aws_util import (
    create_ec2_instance,
    create_key_pair,
    get_or_create_security_group,
    get_validated_ami_id,
    select_region,
    select_vpc,
)
from .config import HostConfig
from .term import Term, run_remote_cmd

# Client code will be deposited here on the remote EC2 instance
SERVER_CLIENT_CODE_HOME = '/opt/dagster/app/'


def get_dagster_home():
    '''Ensures that the user has set a valid DAGSTER_HOME in environment and that it exists
    '''

    dagster_home = os.getenv('DAGSTER_HOME')
    if dagster_home is None:
        Term.fatal(
            '''DAGSTER_HOME is not set! Before continuing, set with e.g.:

export DAGSTER_HOME=~/.dagster

You may want to add this line to your .bashrc or .zshrc file.
'''
        )

    Term.info('Found DAGSTER_HOME in environment at: %s' % dagster_home)

    if not os.path.isdir(dagster_home):
        Term.fatal('The specified DAGSTER_HOME folder does not exist! Create before continuing.')
    return dagster_home


def exit_gracefully(_signum, _frame):
    '''Prevent stack trace spew on Ctrl-C
    '''
    click.echo(click.style('\n\nCommand killed by keyboard interrupt, quitting\n\n', fg='yellow'))
    sys.exit(1)


def rsync_to_remote(key_file_path, local_path, remote_host, remote_path):
    remote_user = 'ubuntu'

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
        '"ssh -i %s"' % key_file_path,
        local_path,
        '%s@%s:%s' % (remote_user, remote_host, remote_path),
    ]
    Term.info('rsyncing local path %s to %s:%s' % (local_path, remote_host, remote_path))
    click.echo('\n' + ' '.join(rsync_command) + '\n')
    subprocess.call(' '.join(rsync_command), shell=True)


@click.group()
def main():
    signal.signal(signal.SIGINT, exit_gracefully)


@main.command()
def init():
    '''🚀 Initialize an EC2 VM to host Dagit'''
    click.echo('\n🌈 Welcome to Dagit + AWS quickstart cloud init!\n')

    # this ensures DAGSTER_HOME exists before we continue
    dagster_home = get_dagster_home()

    already_run = HostConfig.exists(dagster_home)
    prev_config = None
    if already_run:
        click.confirm(
            'dagster-aws has already been initialized! Continue?', default=False, abort=True
        )
        prev_config = HostConfig.load(dagster_home)

    # Get region
    if prev_config and prev_config.region:
        Term.success('Found existing region, continuing with %s' % prev_config.region)
        region = prev_config.region
    else:
        region = select_region()

    client = boto3.client('ec2', region_name=region)
    ec2 = boto3.resource('ec2', region_name=region)

    vpc = select_vpc(client, ec2)

    security_group_id = get_or_create_security_group(client, ec2, vpc)

    ami_id = get_validated_ami_id(client)

    if prev_config and prev_config.key_file_path and os.path.exists(prev_config.key_file_path):
        Term.success(
            'Found existing key pair %s, continuing with %s'
            % (prev_config.key_pair_name, prev_config.key_file_path)
        )
        key_pair_name, key_file_path = prev_config.key_pair_name, prev_config.key_file_path
    else:
        key_pair_name, key_file_path = create_key_pair(client, dagster_home)

    inst = create_ec2_instance(ec2, security_group_id, ami_id, key_pair_name)

    # Save host configuration for future commands
    cfg = HostConfig(
        inst.public_dns_name,
        inst.id,
        region,
        security_group_id,
        key_pair_name,
        key_file_path,
        ami_id,
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
    '''Open an SSH shell on the remote server'''
    dagster_home = get_dagster_home()
    cfg = HostConfig.load(dagster_home)

    # Lands us directly in /opt/dagster (app dir may not exist yet)
    run_remote_cmd(cfg.key_file_path, cfg.remote_host, 'cd /opt/dagster; bash')


@main.command()
@click.option(
    '-p',
    '--post-up-script',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help='Specify a path to a script with post-init actions',
)
def up(post_up_script):
    '''🌱 Sync your Dagster project to the remote server'''
    dagster_home = get_dagster_home()
    cfg = HostConfig.load(dagster_home)

    if cfg.local_path is None:
        cwd = os.getcwd()
        Term.info('Local path not configured; setting to %s' % cwd)
        cfg = cfg._replace(local_path=cwd)
        cfg.save(dagster_home)

    if not os.path.exists(os.path.join(cfg.local_path, 'repository.yaml')):
        Term.fatal('No repository.yaml found in %s, create before continuing.' % cfg.local_path)

    rsync_to_remote(
        cfg.key_file_path,
        cfg.local_path + '/*',  # sync all files/directories in local_path
        cfg.remote_host,
        SERVER_CLIENT_CODE_HOME,
    )

    # If user has supplied a requirements.txt, install after syncing
    if os.path.exists(os.path.join(cfg.local_path, 'requirements.txt')):
        Term.waiting(
            'Found a requirements.txt, ensuring dependencies are installed on remote host...'
        )
        retval = run_remote_cmd(
            cfg.key_file_path,
            cfg.remote_host,
            'export PYTHONPATH=$PYTHONPATH:/opt/dagster/app && '
            'source /opt/dagster/venv/bin/activate && '
            'cd %s && pip install -r requirements.txt' % SERVER_CLIENT_CODE_HOME,
        )

    if post_up_script is not None:
        post_up_script = os.path.expanduser(post_up_script)

        Term.waiting('Copying user post-up script...')
        rsync_to_remote(cfg.key_file_path, post_up_script, cfg.remote_host, '/opt/dagster/')

        Term.waiting('Running user post-up script...')
        retval = run_remote_cmd(
            cfg.key_file_path,
            cfg.remote_host,
            'export PYTHONPATH=$PYTHONPATH:/opt/dagster/app && '
            'source /opt/dagster/venv/bin/activate && '
            'cd /opt/dagster/ && '
            'bash /opt/dagster/%s' % os.path.basename(post_up_script),
        )

    Term.waiting('Testing that pipeline loads correctly on remote host...')
    retval = run_remote_cmd(
        cfg.key_file_path,
        cfg.remote_host,
        'export PYTHONPATH=$PYTHONPATH:/opt/dagster/app && '
        'source /opt/dagster/venv/bin/activate && '
        'cd /opt/dagster/app/ && '
        '/opt/dagster/venv/bin/dagster pipeline list',
    )

    if retval == 0:
        Term.success('Pipeline test succeeded')
    else:
        Term.fatal('Errors in pipeline; fix before proceeding')

    Term.waiting('Restarting dagit systemd service...')
    retval = run_remote_cmd(cfg.key_file_path, cfg.remote_host, 'sudo systemctl restart dagit')
    Term.success('Synchronization succeeded. Opening in browser...')

    # Open dagit in browser, but sleep for a few seconds first to give the service time to finish
    # restarting
    time.sleep(2)
    webbrowser.open_new_tab('http://%s:3000' % cfg.remote_host)


@main.command()
def update_dagster():
    '''Update the remote copy of Dagster'''
    dagster_home = get_dagster_home()
    cfg = HostConfig.load(dagster_home)

    Term.waiting(
        'Running a git pull and make rebuild_dagit on the remote dagster, this may take a while...'
    )
    retval = run_remote_cmd(
        cfg.key_file_path, cfg.remote_host, 'cd /opt/dagster/dagster && git pull'
    )
    if retval == 0:
        Term.info('Dagster git refresh completed! Rebuilding dagit...')
    else:
        Term.fatal('git pull failed')

    retval = run_remote_cmd(
        cfg.key_file_path,
        cfg.remote_host,
        'source /opt/dagster/venv/bin/activate && '
        'cd /opt/dagster/dagster/ && '
        'make rebuild_dagit',
    )
    if retval == 0:
        Term.success('Updating complete!')
    else:
        Term.fatal('Rebuilding dagit failed')


@main.command()
def nuke():
    '''💥 Terminate your EC2 instance'''
    dagster_home = get_dagster_home()

    already_run = HostConfig.exists(dagster_home)

    if not already_run:
        Term.fatal('No existing configuration detected, exiting')

    cfg = HostConfig.load(dagster_home)

    client = boto3.client('ec2', region_name=cfg.region)
    ec2 = boto3.resource('ec2', region_name=cfg.region)

    instances = ec2.instances.filter(InstanceIds=[cfg.instance_id])

    Term.warning('This will terminate the following: ')
    for instance in instances:
        name = None
        for tag in instance.tags:
            if tag.get('Key') == 'Name':
                name = tag.get('Value')
        click.echo('\t%s %s %s' % (instance.id, name, instance.instance_type))

    click.confirm('\nThis step cannot be undone. Continue?', default=False, abort=True)

    Term.waiting('Terminating...')
    instances.terminate()

    # Wipe all instance-related configs
    cfg = cfg._replace(remote_host=None, instance_id=None, ami_id=None, local_path=None)

    # Prompt user to remove key pair
    should_delete_key_pair = click.confirm(
        'Do you also want to remove the key pair %s?' % cfg.key_pair_name
    )
    if should_delete_key_pair:
        client.delete_key_pair(KeyName=cfg.key_pair_name)
        cfg = cfg._replace(key_pair_name=None, key_file_path=None)

    # Prompt user to delete security group also
    should_remove_security_group = click.confirm(
        'Do you also want to remove the security group %s?' % cfg.security_group_id
    )
    if should_remove_security_group:
        client.delete_security_group(GroupId=cfg.security_group_id)
        cfg = cfg._replace(security_group_id=None)

    # Write out updated config
    cfg.save(dagster_home)

    Term.success('Done!')
