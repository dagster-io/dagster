import os
from collections import namedtuple

import six
import terminaltables
import yaml

from dagster import check

from .term import Term

HOST_CONFIG_FILE = 'dagster-aws-config.yaml'


class ConfigMixin(object):
    @classmethod
    def exists(cls, base_path):
        '''Check that the configuration file exists and the key for this config type exists in the
        file
        '''
        cfg_path = os.path.join(base_path, HOST_CONFIG_FILE)
        if not os.path.exists(cfg_path):
            return False

        with open(cfg_path, 'rb') as f:
            record = yaml.safe_load(f)
            if record and cls.KEY in record:
                return True

        return False

    def save(self, base_path):
        '''Serialize configuration to a YAML file for future use
        '''
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        cfg_path = os.path.join(base_path, HOST_CONFIG_FILE)

        record = {}

        if os.path.exists(cfg_path):
            with open(cfg_path, 'rb') as f:
                record = yaml.safe_load(f) or {}

        record[self.KEY] = dict(self._asdict())

        with open(cfg_path, 'wb') as f:
            f.write(six.ensure_binary(yaml.dump(record, default_flow_style=False)))
        Term.info('Saved %s configuration to %s' % (self.TITLE, cfg_path))

    @classmethod
    def load(cls, base_path):
        '''Deserialize the configuration from the YAML config file.
        '''
        filepath = os.path.join(base_path, HOST_CONFIG_FILE)

        if not os.path.exists(filepath):
            Term.fatal('No configuration found, run `dagster-aws init` to get started.')

        with open(filepath, 'rb') as f:
            raw_cfg = yaml.safe_load(f)
        return cls.__new__(cls, **raw_cfg.get(cls.KEY, {}))

    def as_table(self):
        '''Returns a tabulated string representation of this config class
        '''
        as_dict = self._asdict()
        if 'password' in as_dict:
            as_dict['password'] = '<redacted>'

        table_data = [('Config Key', 'Value')] + list(as_dict.items())
        return terminaltables.SingleTable(table_data, title=self.TITLE).table

    def delete(self, base_path):
        '''Remove the configuration for this resource from HOST_CONFIG_FILE
        '''
        if not self.exists(base_path):
            Term.warning('No configuration for %s found, skipping deletion' % self.KEY)
            return False

        cfg_path = os.path.join(base_path, HOST_CONFIG_FILE)
        with open(cfg_path, 'rb') as f:
            record = yaml.safe_load(f) or {}

        if self.KEY in record:
            del record[self.KEY]
            with open(cfg_path, 'wb') as f:
                f.write(six.ensure_binary(yaml.dump(record, default_flow_style=False)))
            Term.info('Removed configuration for %s from %s' % (self.KEY, cfg_path))
            return True

        return False


class RDSConfig(
    namedtuple(
        '_RDSConfig',
        'instance_name instance_type storage_size_gb db_engine db_engine_version instance_uri '
        'db_name username password',
    ),
    ConfigMixin,
):
    TITLE = 'RDS Configuration'
    KEY = 'rds'

    def __new__(
        cls,
        instance_name=None,
        instance_type=None,
        storage_size_gb=20,
        db_engine='postgres',
        db_engine_version='11.6',
        instance_uri=None,
        db_name='dagster',
        username='dagster',
        password=None,
    ):
        return super(RDSConfig, cls).__new__(
            cls,
            instance_name=check.opt_str_param(instance_name, 'instance_name'),
            instance_type=check.opt_str_param(instance_type, 'instance_type'),
            storage_size_gb=check.opt_int_param(storage_size_gb, 'storage_size_gb'),
            db_engine=check.opt_str_param(db_engine, 'db_engine'),
            db_engine_version=check.opt_str_param(db_engine_version, 'db_engine_version'),
            instance_uri=check.opt_str_param(instance_uri, 'instance_uri'),
            db_name=check.opt_str_param(db_name, 'db_name'),
            username=check.opt_str_param(username, 'username'),
            password=check.opt_str_param(password, 'password'),
        )


class EC2Config(
    namedtuple(
        '_HostConfig',
        'remote_host instance_id region security_group_id key_pair_name key_file_path ami_id '
        'local_path',
    ),
    ConfigMixin,
):
    '''Serialize the user's AWS host configuration to a YAML file for future use.
    '''

    TITLE = 'EC2 Configuration'
    KEY = 'ec2'

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
    ):
        return super(EC2Config, cls).__new__(
            cls,
            remote_host=check.opt_str_param(remote_host, 'remote_host'),
            instance_id=check.opt_str_param(instance_id, 'instance_id'),
            region=check.opt_str_param(region, 'region'),
            security_group_id=check.opt_str_param(security_group_id, 'security_group_id'),
            key_pair_name=check.opt_str_param(key_pair_name, 'key_pair_name'),
            key_file_path=check.opt_str_param(key_file_path, 'key_file_path'),
            ami_id=check.opt_str_param(ami_id, 'ami_id'),
            local_path=check.opt_str_param(local_path, 'local_path'),
        )
