# -*- coding: utf-8 -*-
import datetime
import getpass
import os
import time

import boto3
import click
import six
import terminaltables
from botocore.exceptions import ClientError

from .term import Spinner, Term

# Default to northern CA
DEFAULT_REGION = 'us-west-1'

# User can select an EC2 instance type if this is too small
DEFAULT_INSTANCE_TYPE = 't3.medium'

# Ubuntu Server 18.04 LTS (HVM), SSD Volume Type
DEFAULT_AMI = 'ami-08fd8ae3806f09a08'

# User can select an instance type for a PG RDS instance
DEFAULT_RDS_INSTANCE_TYPE = 'db.t3.small'

VPC_CREATION_WARNING = '''Note that this script will not create a VPC on your behalf. If you don't
know what this is, the default is almost certainly what you want. However,
please be aware that the instance we create in your VPC is likely to be
insecure (publicly accessible). For production, you will probably want to set
up a secured instance and VPC!
'''


def get_all_regions():
    '''Retrieves all regions/endpoints that work with EC2
    '''
    response = boto3.client('ec2').describe_regions()
    return sorted([r['RegionName'] for r in response['Regions']])


def select_region(prev_config):
    '''User can select the region in which to instantiate EC2 machine.
    '''
    if prev_config and prev_config.region:
        Term.success('Found existing region, continuing with %s' % prev_config.region)
        return prev_config.region

    all_regions = get_all_regions()

    table = terminaltables.SingleTable(
        [[r] for r in all_regions], title=click.style('Regions', fg='blue')
    )
    table.inner_heading_row_border = False
    click.echo('\n' + table.table)

    return click.prompt(
        'Select an AWS region ' + click.style('[default: %s]' % DEFAULT_REGION, fg='green'),
        type=click.Choice(all_regions),
        default=DEFAULT_REGION,
        show_default=False,
        show_choices=False,
    )


def select_vpc(client, ec2):
    '''User can select the VPC they would like to use for this machine.
    '''
    filters = [{'Name': 'isDefault', 'Values': ['true']}]
    default_vpcs = list(ec2.vpcs.filter(Filters=filters))

    # Will be either zero or one VPC; per boto3 docs,
    # "You cannot have more than one default VPC per Region."
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.create_default_vpc
    if not default_vpcs:
        Term.fatal('AWS account does not have a default VPC; needs manual setup')

    default_vpc = default_vpcs[0].id

    vpcs = []
    for vpc in ec2.vpcs.iterator():
        response = client.describe_vpcs(VpcIds=[vpc.id])
        name = [tag['Value'] for tag in response['Vpcs'][0].get('Tags', []) if tag['Key'] == 'Name']
        if vpc.id == default_vpc:
            name = ['default']
        vpcs.append([vpc.id, name[0] if name else '<none>'])

    table = terminaltables.SingleTable(vpcs, title=click.style('Existing VPCs', fg='blue'))
    table.inner_heading_row_border = False
    click.echo('\n' + table.table)

    vpc = None
    vpc_ids = [vpc[0] for vpc in vpcs]

    Term.info(VPC_CREATION_WARNING)

    vpc = None
    while not vpc:
        vpc = click.prompt(
            '\nSelect an existing VPC ID to use. '
            + click.style('[default: %s]' % default_vpc, fg='green'),
            type=str,
            default=default_vpc,
            show_default=False,
        )
        if vpc not in vpc_ids:
            Term.error('Specified VPC %s does not exist' % vpc)
            vpc = None
    return vpc


def create_security_group(prev_config, client, ec2, vpc):
    '''Allows the user to select a security group, otherwise we create one for the dagit host.
    '''
    if prev_config and prev_config.security_group_id:
        Term.success(
            'Found existing security group, continuing with %s' % (prev_config.security_group_id)
        )
        return prev_config.security_group_id

    now = datetime.datetime.utcnow()
    default_group_name = 'dagster-sg-%s-%s' % (getpass.getuser(), now.strftime("%Y%m%dT%H%M%S"))

    existing_group_names = [
        g['GroupName']
        for g in client.describe_security_groups()['SecurityGroups']
        if g.get('VpcId') == vpc
    ]

    group_name = None
    while not group_name:
        group_name = click.prompt(
            '\nChoose a security group name '
            + click.style('[default is %s]' % default_group_name, fg='green'),
            type=str,
            default=default_group_name,
            show_default=False,
        )

        # Ensure key doesn't already exist
        if group_name in existing_group_names:
            Term.error('Specified security group already exists, won\'t create')
            group_name = None

        else:
            Term.waiting('Creating dagit security group...')
            group = ec2.create_security_group(
                GroupName=group_name, Description='dagit Security Group', VpcId=vpc
            )
            client.authorize_security_group_ingress(
                GroupId=group.id,
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
            group.create_tags(Tags=[{'Key': 'Name', 'Value': group_name}])
            Term.rewind()
            Term.success('Security group created!')
            return group.id


def create_key_pair(prev_config, client, dagster_home):
    '''Ensures we have a key pair in place for creating EC2 instance so that the user can SSH to the
    machine once it is created.
    '''
    if prev_config and prev_config.key_file_path and os.path.exists(prev_config.key_file_path):
        Term.success(
            'Found existing key pair %s, continuing with %s'
            % (prev_config.key_pair_name, prev_config.key_file_path)
        )
        return prev_config.key_pair_name, prev_config.key_file_path

    now = datetime.datetime.utcnow()
    default_key_pair_name = 'dagster-keypair-%s-%s' % (
        getpass.getuser(),
        now.strftime("%Y%m%dT%H%M%S"),
    )

    existing_key_pairs = [k['KeyName'] for k in client.describe_key_pairs()['KeyPairs']]

    key_pair_name = None
    while not key_pair_name:
        key_pair_name = click.prompt(
            '\nChoose a key pair name '
            + click.style('[default is %s]' % default_key_pair_name, fg='green'),
            type=str,
            default=default_key_pair_name,
            show_default=False,
        )

        # Ensure key doesn't already exist
        if key_pair_name in existing_key_pairs:
            Term.error('Specified key pair %s already exists, won\'t create' % key_pair_name)
            key_pair_name = None

        else:
            # key does not exist yet, safe to create
            Term.waiting('Creating new key pair...')
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

            time.sleep(0.4)
            Term.rewind()
            Term.success(
                'Key pair %s created and saved to local file %s!' % (key_pair_name, key_file_path)
            )
            return six.ensure_str(key_pair_name), six.ensure_str(key_file_path)


def get_validated_ami_id(client):
    '''Permit the user to select an AMI to use. We default to using a Ubuntu 16.04 LTS AMI.
    '''

    ami_id = None
    while not ami_id:
        ami_id = click.prompt(
            '\nChoose an AMI to use (must be Debian-based) '
            + click.style('[default is %s (For us-west-1 region only)]' % DEFAULT_AMI, fg='green'),
            type=str,
            default=DEFAULT_AMI,
            show_default=False,
        )

        # Boto will throw a ClientError exception if this AMI doesn't exist.
        try:
            client.describe_images(ImageIds=[ami_id])
        except ClientError:
            Term.error('Specified AMI does not exist in the chosen region, fix to continue')
            ami_id = None

    return six.ensure_str(ami_id)


def create_ec2_instance(client, ec2, security_group_id, ami_id, key_pair_name, use_master):
    '''Actually create the EC2 instance given the provided configuration.
    '''
    click.echo(u'\n🌱 Provisioning an EC2 instance for dagit')

    instance_type = click.prompt(
        '\nChoose an EC2 instance type '
        + click.style('[default is %s]' % DEFAULT_INSTANCE_TYPE, fg='green'),
        type=str,
        default=DEFAULT_INSTANCE_TYPE,
        show_default=False,
    )

    ec2_default_name = 'dagit-ec2-%s' % getpass.getuser()
    ec2_instance_name = click.prompt(
        '\nChoose an EC2 instance name '
        + click.style('[default is %s]' % ec2_default_name, fg='green'),
        type=str,
        default=ec2_default_name,
        show_default=False,
    )

    init_script_name = 'init.sh' if use_master else 'init-stable.sh'

    # Here we actually create the EC2 instance
    Term.waiting('Creating dagit EC2 instance. This can take a couple of minutes...')
    with Spinner():
        with open(os.path.join(os.path.dirname(__file__), 'shell', init_script_name), 'rb') as f:
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
        waiter = client.get_waiter('instance_status_ok')
        waiter.wait(InstanceIds=[inst.id])

        # Add name tag to instance after creation
        ec2.create_tags(Resources=[inst.id], Tags=[{'Key': 'Name', 'Value': ec2_instance_name}])

        # Load details like public DNS name, etc.
        inst.reload()

    Term.rewind()
    Term.success('dagit EC2 instance %s launched!' % inst.id)

    return inst


def create_rds_instance(dagster_home, region):
    '''Creates an RDS PostgreSQL instance.

    Returns:
    RDSConfig object
    '''
    from .config import RDSConfig

    if RDSConfig.exists(dagster_home):
        prev_config = RDSConfig.load(dagster_home)
        Term.success('Found existing RDS database, continuing with %s' % (prev_config.instance_uri))
        return prev_config

    rds = boto3.client('rds', region_name=region)

    use_rds = click.confirm(
        '\nDo you want to use RDS PostgreSQL for run storage? (default: use filesystem) '
        + click.style('[y/N]', fg='green'),
        default=False,
        show_default=False,
    )
    if not use_rds:
        return None

    def generate_password(pass_len=16):
        client = boto3.client('secretsmanager')
        response = client.get_random_password(
            PasswordLength=pass_len, ExcludePunctuation=True, IncludeSpace=False
        )
        return response['RandomPassword']

    instance_type = click.prompt(
        '\nChoose an RDS instance type - see https://aws.amazon.com/rds/instance-types/ '
        + click.style('[default is %s]' % DEFAULT_RDS_INSTANCE_TYPE, fg='green'),
        type=str,
        default=DEFAULT_RDS_INSTANCE_TYPE,
        show_default=False,
    )

    default_name = 'dagster-rds-%s' % getpass.getuser()
    instance_name = click.prompt(
        '\nChoose an RDS instance name '
        + click.style('[default is %s]' % default_name, fg='green'),
        type=str,
        default=default_name,
        show_default=False,
    )

    rds_config = RDSConfig(
        instance_name=instance_name, instance_type=instance_type, password=generate_password()
    )

    Term.waiting(
        u'Creating Dagster RDS instance. This unfortunately takes quite a while, 5+ minutes, so '
        u'grab some 🍿...'
    )
    with Spinner():
        rds.create_db_instance(
            AllocatedStorage=rds_config.storage_size_gb,
            DBInstanceClass=rds_config.instance_type,
            DBInstanceIdentifier=rds_config.instance_name,
            DBName=rds_config.db_name,
            Engine=rds_config.db_engine,
            EngineVersion=rds_config.db_engine_version,
            MasterUsername=rds_config.username,
            MasterUserPassword=rds_config.password,
        )
        waiter_rds = rds.get_waiter('db_instance_available')
        waiter_rds.wait(DBInstanceIdentifier=instance_name)
        response = rds.describe_db_instances(DBInstanceIdentifier=instance_name)
        instance_uri = response['DBInstances'][0]['Endpoint']['Address']

    Term.rewind()
    Term.success('Dagster RDS instance %s launched!' % instance_uri)

    return rds_config._replace(instance_uri=instance_uri)
