import base64
import getpass
import os

import boto3
import dagster_aws
import pytest
import six
from dagster_aws.cli.aws_util import (
    DEFAULT_AMI,
    DEFAULT_INSTANCE_TYPE,
    VPC_CREATION_WARNING,
    create_ec2_instance,
    create_key_pair,
    create_rds_instance,
    create_security_group,
    get_validated_ami_id,
    select_region,
    select_vpc,
)
from dagster_aws.cli.config import EC2Config, RDSConfig
from moto import mock_ec2, mock_rds, mock_secretsmanager
from six import StringIO


@mock_ec2
def test_select_region(monkeypatch, capsys):
    region = 'us-east-1'
    monkeypatch.setattr(
        'sys.stdin', StringIO('does-not-exist\n{region}\n'.format(region=region)),
    )
    res = select_region(None)
    assert res == region

    captured = capsys.readouterr()
    assert 'Error: invalid choice: does-not-exist' in captured.out


@mock_ec2
def test_select_region_prev_config(capsys):
    region = 'us-east-1'
    prev_config = EC2Config(region=region)
    assert select_region(prev_config) == region
    captured = capsys.readouterr()
    assert 'Found existing region, continuing with {region}'.format(region=region) in captured.out


@mock_ec2
def test_select_vpc(monkeypatch, capsys):
    client = boto3.client('ec2', region_name='us-east-1')
    ec2 = boto3.resource('ec2', region_name='us-east-1')

    filters = [{'Name': 'isDefault', 'Values': ['true']}]
    default_vpcs = list(ec2.vpcs.filter(Filters=filters))  # pylint: disable=no-member

    default_vpc = default_vpcs[0].id
    monkeypatch.setattr(
        'sys.stdin', StringIO('does-not-exist\n{default_vpc}\n'.format(default_vpc=default_vpc)),
    )
    vpc = select_vpc(client, ec2)

    captured = capsys.readouterr()

    assert vpc == default_vpc
    assert VPC_CREATION_WARNING in captured.out
    assert 'Select an existing VPC ID to use' in captured.out
    assert 'Specified VPC does-not-exist does not exist' in captured.out

    # Test missing default VPCs
    for vpc in default_vpcs:
        client.delete_vpc(VpcId=vpc.id)

    with pytest.raises(SystemExit) as exc_info:
        select_vpc(client, ec2)

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert 'AWS account does not have a default VPC' in captured.err


@mock_ec2
def test_select_vpc_created(monkeypatch):
    client = boto3.client('ec2', region_name='us-east-1')
    ec2 = boto3.resource('ec2', region_name='us-east-1')

    vpc = ec2.create_vpc(CidrBlock='172.16.0.0/16')  # pylint: disable=no-member
    monkeypatch.setattr(
        'sys.stdin', StringIO('{vpc_id}\n'.format(vpc_id=vpc.id)),
    )
    selected_vpc = select_vpc(client, ec2)
    assert vpc.id == selected_vpc


@mock_ec2
def test_create_security_groups(monkeypatch, capsys):
    client = boto3.client('ec2', region_name='us-east-1')
    ec2 = boto3.resource('ec2', region_name='us-east-1')

    filters = [{'Name': 'isDefault', 'Values': ['true']}]
    default_vpc = list(ec2.vpcs.filter(Filters=filters))[0].id  # pylint: disable=no-member

    print(
        "client.describe_security_groups()['SecurityGroups']",
        client.describe_security_groups()['SecurityGroups'],
    )

    monkeypatch.setattr(
        'sys.stdin', StringIO('default\nmynewcoolgroup\n'),
    )
    prev_config = None
    res = create_security_group(prev_config, client, ec2, default_vpc)

    filters = [{'Name': 'isDefault', 'Values': ['true']}]
    sg_described = client.describe_security_groups(GroupIds=[res])['SecurityGroups'][0]

    assert sg_described['Description'] == 'dagit Security Group'
    assert sg_described['GroupName'] == 'mynewcoolgroup'

    assert sg_described['IpPermissions'] == [
        {
            'FromPort': 3000,
            'IpProtocol': 'tcp',
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
            'ToPort': 3000,
            'UserIdGroupPairs': [],
        },
        {
            'FromPort': 22,
            'IpProtocol': 'tcp',
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
            'ToPort': 22,
            'UserIdGroupPairs': [],
        },
    ]
    assert sg_described['Tags'] == [{'Key': 'Name', 'Value': 'mynewcoolgroup'}]

    next_group = 'myothercoolgroup'
    prev_config = EC2Config(security_group_id=next_group)
    assert create_security_group(prev_config, client, ec2, default_vpc) == next_group
    captured = capsys.readouterr()
    assert (
        'Found existing security group, continuing with {group}'.format(group=next_group)
        in captured.out
    )


@mock_ec2
def test_create_key_pair(monkeypatch, capsys, tmp_path):
    tmp_path = str(tmp_path)

    client = boto3.client('ec2', region_name='us-east-1')

    existing = 'foobar-keypair'
    client.create_key_pair(KeyName=existing)

    new_keypair = 'my-new-keypair'
    monkeypatch.setattr(
        'sys.stdin',
        StringIO('{existing}\n{new_keypair}\n'.format(existing=existing, new_keypair=new_keypair)),
    )

    prev_config = None
    res = create_key_pair(prev_config, client, tmp_path)
    assert res[0] == new_keypair
    assert res[1] == os.path.join(tmp_path, 'keys/%s.pem' % new_keypair)

    captured = capsys.readouterr()
    assert (
        'Specified key pair {existing} already exists, won\'t create'.format(existing=existing)
        in captured.out
    )

    # test existing
    key_file_path = os.path.join(tmp_path, 'mykey')
    open(key_file_path, 'a').close()
    prev_config = EC2Config(key_pair_name='mykey', key_file_path=key_file_path)
    res = create_key_pair(prev_config, client, tmp_path)
    assert res == ('mykey', key_file_path)

    captured = capsys.readouterr()
    assert 'Found existing key pair mykey' in captured.out


@mock_ec2
def test_get_validated_ami_id(monkeypatch, capsys):
    client = boto3.client('ec2', region_name='us-east-1')

    source_ami_id = 'ami-03cf127a'

    monkeypatch.setattr(
        'sys.stdin',
        StringIO('does-not-exist\n{source_ami_id}\n'.format(source_ami_id=source_ami_id)),
    )
    res = get_validated_ami_id(client)

    assert res == source_ami_id
    captured = capsys.readouterr()

    prompt = (
        'Choose an AMI to use (must be Debian-based) [default is %s (For us-west-1 region only)]:'
        % DEFAULT_AMI
    )
    assert captured.out.strip() == u'{prompt} \u274C  Specified AMI does not exist in the chosen region, fix to continue\n\n{prompt}'.format(
        prompt=prompt
    )


@mock_ec2
def test_create_ec2_instance(monkeypatch):
    def _validate_user_data(ec2_instance, script_name):
        # Validate user data is init script
        with open(
            os.path.join(os.path.dirname(dagster_aws.cli.aws_util.__file__), 'shell', script_name),
            'rb',
        ) as f:
            init_script = six.ensure_str(f.read())

        user_data_b64 = ec2_instance.describe_attribute(Attribute='userData')['UserData']['Value']
        user_data_str = six.ensure_str(base64.b64decode(user_data_b64))

        assert user_data_str == init_script

    client = boto3.client('ec2', region_name='us-west-1')
    ec2 = boto3.resource('ec2', region_name='us-west-1')

    filters = [{'Name': 'isDefault', 'Values': ['true']}]
    default_vpc = list(ec2.vpcs.filter(Filters=filters))[0].id  # pylint: disable=no-member

    keypair_name = 'foobar-keypair'
    client.create_key_pair(KeyName=keypair_name)

    # Test init-stable.sh
    instance_type = 't3.large'
    monkeypatch.setattr(
        'sys.stdin',
        StringIO('\n{instance_type}\nmycoolinstance\n'.format(instance_type=instance_type)),
    )
    prev_config = None
    sg_id = create_security_group(prev_config, client, ec2, default_vpc)

    ec2_instance = create_ec2_instance(
        client, ec2, sg_id, DEFAULT_AMI, keypair_name, use_master=False
    )

    assert ec2_instance.instance_type == instance_type
    assert ec2_instance.image_id == DEFAULT_AMI
    assert ec2_instance.tags == [{'Key': 'Name', 'Value': 'mycoolinstance'}]
    assert sg_id in [g['GroupId'] for g in ec2_instance.security_groups]
    _validate_user_data(ec2_instance, 'init-stable.sh')

    # Test init.sh
    monkeypatch.setattr(
        'sys.stdin', StringIO('\n\n\n'),
    )
    prev_config = None

    ec2_instance = create_ec2_instance(
        client, ec2, sg_id, DEFAULT_AMI, keypair_name, use_master=True
    )

    assert ec2_instance.instance_type == DEFAULT_INSTANCE_TYPE
    assert ec2_instance.image_id == DEFAULT_AMI
    assert sg_id in [g['GroupId'] for g in ec2_instance.security_groups]
    assert ec2_instance.tags == [{'Key': 'Name', 'Value': 'dagit-ec2-%s' % getpass.getuser()}]
    _validate_user_data(ec2_instance, 'init.sh')


@mock_rds
@mock_secretsmanager
def test_create_rds_instance(monkeypatch, tmp_path):
    tmp_path = str(tmp_path)

    monkeypatch.setattr(
        'sys.stdin', StringIO('\n'),
    )
    region = 'us-east-1'
    rds = boto3.client('rds', region_name=region)

    # Test don't create
    rds_instance = create_rds_instance(tmp_path, region)
    assert rds_instance is None

    # Test create
    instance_type = 'db.t3.2xlarge'
    instance_name = 'foobardb'
    monkeypatch.setattr(
        'sys.stdin',
        StringIO(
            'Y\n{instance_type}\n{instance_name}\n'.format(
                instance_type=instance_type, instance_name=instance_name
            )
        ),
    )
    rds_instance = create_rds_instance(tmp_path, 'us-east-1')
    db_instance = rds.describe_db_instances(DBInstanceIdentifier=instance_name)['DBInstances'][0]

    assert rds_instance.instance_name == instance_name
    assert rds_instance.instance_type == instance_type
    assert rds_instance.storage_size_gb == 20
    assert rds_instance.db_engine == 'postgres'
    assert rds_instance.db_name == 'dagster'
    assert rds_instance.username == 'dagster'

    assert db_instance['DBInstanceIdentifier'] == instance_name
    assert db_instance['DBInstanceClass'] == instance_type
    assert db_instance['Engine'] == 'postgres'
    assert db_instance['DBInstanceStatus'] == 'available'
    assert db_instance['MasterUsername'] == 'dagster'
    assert db_instance['DBName'] == 'dagster'
    assert db_instance['Endpoint']['Port'] == 5432

    assert db_instance['Endpoint']['Address'] == rds_instance.instance_uri
    assert db_instance['AllocatedStorage'] == rds_instance.storage_size_gb
    assert db_instance['EngineVersion'] == rds_instance.db_engine_version


def test_create_rds_instance_already_exists(capsys, tmp_path):

    rds_config = RDSConfig(
        instance_name='foo', instance_uri='foo-bar.amazonaws.com', password='baz'
    )
    rds_config.save(str(tmp_path))
    prev_config = create_rds_instance(str(tmp_path), 'us-west-1')
    assert prev_config == rds_config

    captured = capsys.readouterr()
    assert 'Found existing RDS database, continuing with foo-bar.amazonaws.com' in captured.out
