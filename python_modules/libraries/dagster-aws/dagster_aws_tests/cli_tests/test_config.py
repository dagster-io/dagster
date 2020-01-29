import os
import uuid

import yaml
from dagster_aws.cli.config import HOST_CONFIG_FILE, EC2Config, RDSConfig

from dagster import seven


def test_write_configs():
    ec2_config = EC2Config(
        remote_host='foo',
        region='us-west-1',
        security_group_id='sg-12345',
        key_pair_name='foobar',
        key_file_path='/some/path',
        ami_id='ami-12345',
    )

    rds_config = RDSConfig(
        instance_name='foo', instance_uri='foo-bar.amazonaws.com', password='baz'
    )

    # Ensure unique dir for test
    tmp_dir = os.path.join(seven.get_system_temp_directory(), uuid.uuid4().hex)
    outfile = os.path.join(tmp_dir, HOST_CONFIG_FILE)

    ec2_config.save(tmp_dir)
    rds_config.save(tmp_dir)

    with open(outfile) as f:
        record = yaml.safe_load(f)

    ec2_config_dict = record['ec2']
    rds_config_dict = record['rds']

    assert ec2_config_dict['remote_host'] == 'foo'
    assert ec2_config_dict['region'] == 'us-west-1'
    assert ec2_config_dict['security_group_id'] == 'sg-12345'
    assert ec2_config_dict['key_pair_name'] == 'foobar'
    assert ec2_config_dict['key_file_path'] == '/some/path'
    assert ec2_config_dict['ami_id'] == 'ami-12345'
    assert EC2Config.load(tmp_dir) == EC2Config(**ec2_config_dict) == ec2_config

    assert rds_config_dict['instance_name'] == 'foo'
    assert rds_config_dict['instance_uri'] == 'foo-bar.amazonaws.com'
    assert rds_config_dict['storage_size_gb'] == 20
    assert rds_config_dict['db_engine'] == 'postgres'
    assert rds_config_dict['db_engine_version'] == '11.5'
    assert RDSConfig.load(tmp_dir) == RDSConfig(**rds_config_dict)

    # Delete both configs
    res = rds_config.delete(tmp_dir)
    assert res
    assert not RDSConfig.exists(tmp_dir)
    res = ec2_config.delete(tmp_dir)
    assert res
    assert not EC2Config.exists(tmp_dir)

    # Try to delete non-existent config
    res = rds_config.delete(tmp_dir)
    assert not res


def test_table():
    cfg = EC2Config(
        remote_host='foo',
        region='us-west-1',
        security_group_id='sg-12345',
        key_pair_name='foobar',
        key_file_path='/some/path',
        ami_id='ami-12345',
    )

    cfg_table = cfg.as_table()
    assert 'EC2 Configuration' in cfg_table

    rds_config = RDSConfig(
        instance_name='foo', instance_uri='foo-bar.amazonaws.com', password='top secret'
    )
    rds_config_table = rds_config.as_table()
    assert 'RDS Configuration' in rds_config_table
    assert 'top secret' not in rds_config_table
    assert '<redacted>' in rds_config_table
