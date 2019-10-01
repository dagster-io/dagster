import os
from collections import namedtuple

import six
import yaml

from dagster import check

from .term import Term

HOST_CONFIG_FILE = 'dagster-aws-config.yaml'


class RDSConfig(namedtuple('_RDSConfig', 'instance_name instance_uri password')):
    def __new__(cls, instance_name=None, instance_uri=None, password=None):
        return super(RDSConfig, cls).__new__(
            cls,
            instance_name=check.opt_str_param(instance_name, 'instance_name'),
            instance_uri=check.opt_str_param(instance_uri, 'instance_uri'),
            password=check.opt_str_param(password, 'password'),
        )


class HostConfig(
    namedtuple(
        '_HostConfig',
        'remote_host instance_id region security_group_id key_pair_name key_file_path ami_id '
        'local_path rds_config',
    )
):
    '''Serialize the user's AWS host configuration to a YAML file for future use.
    '''

    def __new__(
        cls,
        remote_host=None,
        instance_id=None,
        region=None,
        security_group_id=None,
        key_pair_name=None,
        key_file_path=None,
        ami_id=None,
        local_path=None,
        rds_config=None,
    ):
        # For when we restore this from a YAML config file
        if isinstance(rds_config, dict):
            rds_config = RDSConfig(**rds_config)

        return super(HostConfig, cls).__new__(
            cls,
            remote_host=check.opt_str_param(remote_host, 'remote_host'),
            instance_id=check.opt_str_param(instance_id, 'instance_id'),
            region=check.opt_str_param(region, 'region'),
            security_group_id=check.opt_str_param(security_group_id, 'security_group_id'),
            key_pair_name=check.opt_str_param(key_pair_name, 'key_pair_name'),
            key_file_path=check.opt_str_param(key_file_path, 'key_file_path'),
            ami_id=check.opt_str_param(ami_id, 'ami_id'),
            local_path=check.opt_str_param(local_path, 'local_path'),
            rds_config=check.opt_inst_param(
                rds_config, 'rds_config', RDSConfig, default=RDSConfig()
            ),
        )

    @staticmethod
    def exists(dagster_home):
        cfg_path = os.path.join(dagster_home, HOST_CONFIG_FILE)
        return os.path.exists(cfg_path)

    def save(self, dagster_home):
        '''Serialize configuration to a YAML file for future use
        '''
        cfg_path = os.path.join(dagster_home, HOST_CONFIG_FILE)
        with open(cfg_path, 'wb') as f:
            output_record = dict(self._asdict())
            output_record['rds_config'] = dict(output_record['rds_config']._asdict())
            f.write(six.ensure_binary(yaml.dump(output_record, default_flow_style=False)))
        Term.info('Saved host configuration to %s' % cfg_path)

    @staticmethod
    def load(dagster_home):
        cfg_path = os.path.join(dagster_home, HOST_CONFIG_FILE)
        with open(cfg_path, 'rb') as f:
            raw_cfg = yaml.load(f)
        return HostConfig(**raw_cfg)
