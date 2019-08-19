# -*- coding: utf-8 -*-

import datetime
import os
import signal
import subprocess
import sys

import boto3
import click
import six

from botocore.exceptions import ClientError

from .config import HostConfig
from .term import Spinner, Term


# Default to northern CA
DEFAULT_REGION = 'us-west-1'

# User can select an EC2 instance type if this is too small
DEFAULT_INSTANCE_TYPE = 't3.medium'

# We'll create this security group if it doesn't exist
DEFAULT_SECURITY_GROUP = 'dagit-sg'

# Ubuntu LTS
DEFAULT_AMI = 'ami-09eb5e8a83c7aa890'

# Dagit EC2 machine name
DAGIT_EC2_NAME = 'dagit-ec2'


def get_dagster_home():
    '''Ensures that the user has set a valid DAGSTER_HOME in environment and that it exists
    '''
    dagster_home = os.getenv('DAGSTER_HOME')
    if not dagster_home:
        Term.fatal(
            '''DAGSTER_HOME is not set! Before continuing, set with e.g.:

export DAGSTER_HOME=~/.dagster

You may want to add this line to your .bashrc or .zshrc file.
'''
        )
    else:
        Term.info('Found DAGSTER_HOME in environment at: %s\n' % dagster_home)

    if not os.path.isdir(dagster_home):
        Term.fatal('The specified DAGSTER_HOME folder does not exist! Create before continuing.')
    return dagster_home


def get_all_regions():
    '''Retrieves all regions/endpoints that work with EC2
    '''
    response = boto3.client('ec2').describe_regions()
    return sorted([r['RegionName'] for r in response['Regions']])


def select_region():
    '''User can select the region in which to instantiate EC2 machine.
    '''
    regions = click.Choice(get_all_regions())

    return click.prompt(
        'Select an AWS region ' + click.style('[default: %s]' % DEFAULT_REGION, fg='green'),
        type=regions,
        default=DEFAULT_REGION,
        show_default=False,
        show_choices=True,
    )


def select_vpc(client, ec2):
    '''User can select the VPC they would like to use for this machine.
    '''
    filters = [{'Name': 'isDefault', 'Values': ['true']}]
    default_vpcs = list(ec2.vpcs.filter(Filters=filters))

    if not default_vpcs:
        Term.fatal('AWS account does not have a default VPC; needs manual setup')
    elif len(default_vpcs) > 1:
        Term.fatal('AWS account has multiple default VPCs; needs manual setup')

    default_vpc = default_vpcs[0]

    vpc_names = []
    for vpc in ec2.vpcs.iterator():
        response = client.describe_vpcs(VpcIds=[vpc.id])
        name = [tag['Value'] for tag in response['Vpcs'][0].get('Tags', []) if tag['Key'] == 'Name']
        vpc_names.append('%s (%s)' % (vpc.id, name[0]) if name else vpc.id)

    vpc = click.prompt(
        '\nSelect a VPC '
        + click.style('[default: %s]' % default_vpc.id, fg='green')
        + '\n\n'
        + click.style('  Existing VPCs:\n  ', fg='blue')
        + '\n  '.join(vpc_names),
        type=str,
        default=default_vpc,
        show_default=False,
    )
    return vpc


def get_or_create_security_group(client, ec2, vpc):
    '''Allows the user to select a security group, otherwise we create one for the dagit host.
    '''
    groups = [
        g for g in client.describe_security_groups()['SecurityGroups'] if g['VpcId'] == vpc.id
    ]

    for group in groups:
        if group['GroupName'] == DEFAULT_SECURITY_GROUP:
            Term.success(
                'Found existing dagit security group, continuing with %s' % group['GroupId']
            )
            return group['GroupId']

    groups_str = ['%s (New security group)' % DEFAULT_SECURITY_GROUP] + [
        '%s (%s)' % (g['GroupId'], g['GroupName']) for g in groups
    ]

    sg = click.prompt(
        '\nSelect a security group ID: '
        + click.style(
            '[default: create new security group %s]' % DEFAULT_SECURITY_GROUP, fg='green'
        )
        + '\n\n'
        + click.style('  Existing security groups:\n  ', fg='blue')
        + '\n  '.join(groups_str),
        type=str,
        default=DEFAULT_SECURITY_GROUP,
        show_default=False,
    )

    if sg == DEFAULT_SECURITY_GROUP:
        Term.waiting('Creating dagit security group...')
        group = ec2.create_security_group(
            GroupName=DEFAULT_SECURITY_GROUP, Description='dagit Security Group', VpcId=vpc.id
        )
        group.authorize_ingress(
            GroupName=DEFAULT_SECURITY_GROUP,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 3000,
                    'ToPort': 3000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP'}],
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH'}],
                },
            ],
        )
        group.create_tags(Tags=[{'Key': 'Name', 'Value': DEFAULT_SECURITY_GROUP}])
        Term.success('Security group created!')

    return sg


def create_key_pair(client, dagster_home):
    '''Ensures we have a key pair in place for creating EC2 instance so that the user can SSH to the
    machine once it is created.
    '''
    now = datetime.datetime.utcnow()
    default_key_pair_name = 'dagit-key-pair-%s' % now.strftime("%Y%m%dT%H%M%S")

    Term.waiting('Creating new key pair...')

    existing_key_pairs = [k['KeyName'] for k in client.describe_key_pairs()['KeyPairs']]

    key_pair_name = None
    while not key_pair_name:
        key_pair_name = click.prompt(
            'Key pair name ' + click.style('[default is %s]' % default_key_pair_name, fg='green'),
            type=str,
            default=default_key_pair_name,
            show_default=False,
        )

        # Ensure key doesn't already exist
        if key_pair_name in existing_key_pairs:
            Term.error('Specified key pair already exists, won\'t create')
            key_pair_name = None

        else:
            # key does not exist yet, safe to create
            keypair = client.create_key_pair(KeyName=key_pair_name)

            key_directory = os.path.join(dagster_home, 'keys')
            key_file_path = os.path.join(key_directory, '%s.pem' % key_pair_name)

            # Ensure key directory exists
            if not os.path.exists(key_directory):
                os.makedirs(key_directory)

            # Write key material and ensure appropriate permissions are set
            with open(key_file_path, 'wb') as f:
                f.write(six.ensure_binary(keypair['KeyMaterial']))
            os.chmod(key_file_path, 0o600)

            Term.success(
                'Key pair %s created and saved to local file %s!' % (key_pair_name, key_file_path)
            )
            return key_pair_name, key_file_path


def get_validated_ami_id(client):
    '''Permit the user to select an AMI to use. This is currently unused, as instead we default to
    using a Ubuntu 16.04 LTS AMI.
    '''
    ami_id = None
    while not ami_id:
        ami_id = click.prompt(
            '\nChoose an AMI to use (must be Debian-based) '
            + click.style('[default is %s]' % DEFAULT_AMI, fg='green'),
            type=str,
            default=DEFAULT_AMI,
            show_default=False,
        )

        # Boto will throw a ClientError exception if this AMI doesn't exist.
        try:
            client.describe_images(ImageIds=[ami_id])
        except ClientError:
            Term.error('Specified AMI does not exist, fix to continue')
            ami_id = None

    return ami_id


def create_ec2_instance(ec2, security_group_id, ami_id, key_pair_name):
    '''Actually create the EC2 instance given the provided configuration.
    '''
    click.echo('\n🌱 Provisioning an EC2 instance for dagit')

    instance_type = click.prompt(
        '\nChoose an EC2 instance type '
        + click.style('[default is %s]' % DEFAULT_INSTANCE_TYPE, fg='green'),
        type=str,
        default=DEFAULT_INSTANCE_TYPE,
        show_default=False,
    )

    Term.waiting('Creating dagit EC2 instance...')
    click.echo(
        '  '
        + '\n  '.join(
            [
                'AMI: %s' % ami_id,
                'Instance Type: %s' % instance_type,
                'Security Group: %s' % security_group_id,
                'Key Pair: %s' % key_pair_name,
            ]
        )
    )

    # Here we actually create the EC2 instance
    with Spinner():
        with open(os.path.join(os.path.dirname(__file__), 'shell', 'init.sh'), 'rb') as f:
            init_script = six.ensure_str(f.read())

        instances = ec2.create_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            MaxCount=1,
            MinCount=1,
            SecurityGroupIds=[security_group_id],
            KeyName=key_pair_name,
            UserData=init_script,
        )
        inst = instances[0]
        inst.wait_until_running()

        ec2.create_tags(Resources=[inst.id], Tags=[{'Key': 'Name', 'Value': DAGIT_EC2_NAME}])

        # Load details like public DNS name, etc.
        inst.reload()

    Term.success('dagit EC2 instance %s launched!' % inst.id)
    return inst


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

    region = select_region()

    client = boto3.client('ec2', region_name=region)
    ec2 = boto3.resource('ec2', region_name=region)

    vpc = select_vpc(client, ec2)

    security_group_id = get_or_create_security_group(client, ec2, vpc)

    # For now, will force users to use a specific Ubuntu AMI
    ami_id = DEFAULT_AMI  # get_validated_ami_id(client)

    key_pair_name, key_file_path = create_key_pair(client, dagster_home)

    inst = create_ec2_instance(ec2, security_group_id, ami_id, key_pair_name)

    # Save host configuration for future commands
    cfg = HostConfig(
        inst.public_dns_name, region, security_group_id, key_pair_name, key_file_path, ami_id
    )
    cfg.save(dagster_home)

    click.echo(click.style('🚀 To connect, just use: dagit-aws shell\n', fg='green'))


@main.command()
def shell():
    dagster_home = get_dagster_home()
    cfg = HostConfig.load(dagster_home)

    ssh_cmd = 'ssh -i %s ubuntu@%s' % (cfg.key_file_path, cfg.public_dns_name)
    Term.waiting('Connecting to host...\n%s' % ssh_cmd)
    subprocess.call(ssh_cmd, shell=True)
