import os
import yaml

from collections import namedtuple

import six

from dagster import check

from .term import Term


HOST_CONFIG_FILE = '.dagit-aws-config'


class HostConfig(
    namedtuple(
        '_HostConfig',
        'public_dns_name instance_id region security_group_id key_pair_name key_file_path ami_id local_path',
    )
):
    '''Serialize the user's AWS host configuration to a YAML file for future use.
    '''

    def __new__(
        cls,
        public_dns_name=None,
        instance_id=None,
        region=None,
        security_group_id=None,
        key_pair_name=None,
        key_file_path=None,
        ami_id=None,
        local_path=None,
    ):
        return super(HostConfig, cls).__new__(
            cls,
            public_dns_name=check.opt_str_param(public_dns_name, 'public_dns_name'),
            instance_id=check.opt_str_param(instance_id, 'instance_id'),
            region=check.opt_str_param(region, 'region'),
            security_group_id=check.opt_str_param(security_group_id, 'security_group_id'),
            key_pair_name=check.opt_str_param(key_pair_name, 'key_pair_name'),
            key_file_path=check.opt_str_param(key_file_path, 'key_file_path'),
            ami_id=check.opt_str_param(ami_id, 'ami_id'),
            local_path=check.opt_str_param(local_path, 'local_path'),
        )

    @staticmethod
    def exists(dagster_home):
        cfg_path = os.path.join(dagster_home, HOST_CONFIG_FILE)
        return os.path.exists(cfg_path)

    def save(self, dagster_home):
        # Save configuration to a file for future use
        cfg_path = os.path.join(dagster_home, HOST_CONFIG_FILE)
        with open(cfg_path, 'wb') as f:
            output_record = {
                'dagit-aws-host': {
                    'public_dns_name': self.public_dns_name,
                    'instance_id': self.instance_id,
                    'region': self.region,
                    'security_group_id': self.security_group_id,
                    'key_pair_name': self.key_pair_name,
                    'key_file_path': self.key_file_path,
                    'ami_id': self.ami_id,
                    'local_path': self.local_path,
                }
            }
            f.write(six.ensure_binary(yaml.dump(output_record, default_flow_style=False)))
        Term.info('Saved host configuration to %s' % cfg_path)

    @staticmethod
    def load(dagster_home):
        cfg_path = os.path.join(dagster_home, HOST_CONFIG_FILE)
        with open(cfg_path, 'rb') as f:
            raw_cfg = yaml.load(f)
        return HostConfig(**raw_cfg['dagit-aws-host'])
