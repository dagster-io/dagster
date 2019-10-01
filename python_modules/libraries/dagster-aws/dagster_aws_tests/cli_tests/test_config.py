import os

import yaml
from dagster_aws.cli.config import HOST_CONFIG_FILE, HostConfig, RDSConfig

from dagster import seven


def test_host_config():
    rds_config = RDSConfig(
        instance_name='foo', instance_uri='foo-bar.amazonaws.com', password='baz'
    )

    cfg = HostConfig(
        remote_host='foo',
        region='us-west-1',
        security_group_id='sg-12345',
        key_pair_name='foobar',
        key_file_path='/some/path',
        ami_id='ami-12345',
        rds_config=rds_config,
    )

    tmp_dir = seven.get_system_temp_directory()
    outfile = os.path.join(tmp_dir, HOST_CONFIG_FILE)

    cfg.save(tmp_dir)

    with open(outfile) as f:
        configs = yaml.load(f)

    assert configs['remote_host'] == 'foo'
    assert configs['region'] == 'us-west-1'
    assert configs['security_group_id'] == 'sg-12345'
    assert configs['key_pair_name'] == 'foobar'
    assert configs['key_file_path'] == '/some/path'
    assert configs['ami_id'] == 'ami-12345'

    res = cfg.load(tmp_dir)
    assert res == HostConfig(**configs)
    assert res.rds_config == rds_config
