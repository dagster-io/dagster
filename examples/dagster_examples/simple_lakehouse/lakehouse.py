import glob
import os
from typing import Tuple

import boto3
import pandas as pd
from dagster_pyspark import pyspark_resource
from lakehouse import Lakehouse, TypeStoragePolicy
from pandas import DataFrame as PandasDF
from pyspark.sql import DataFrame as SparkDF

from dagster import ModeDefinition, PresetDefinition, resource


@resource(config={'bucket': str, 'prefix': str})
def s3_storage(init_context):
    return S3Storage(init_context.resource_config)


class S3Storage:
    def __init__(self, config):
        self._bucket = config['bucket']
        self._prefix = config['prefix']

    @property
    def bucket(self):
        return self._bucket

    def get_key(self, path: Tuple[str, ...]):
        return '/'.join((self._prefix,) + path)

    def get_path(self, path: Tuple[str, ...]):
        return '/'.join((self._bucket, self._prefix) + path)


@resource(config={'root': str})
def local_file_system_storage(init_context):
    return LocalFileSystemStorage(init_context.resource_config)


class LocalFileSystemStorage:
    def __init__(self, config):
        self._root = config['root']

    def get_fs_path(self, path: Tuple[str, ...]) -> str:
        return os.path.join(self._root, *(path[:-1]), path[-1])


class PandasDFLocalFileSystemPolicy(TypeStoragePolicy):
    @classmethod
    def in_memory_type(cls):
        return PandasDF

    @classmethod
    def storage_definition(cls):
        return local_file_system_storage

    @classmethod
    def save(
        cls, obj: PandasDF, storage: LocalFileSystemStorage, path: Tuple[str, ...], _resources
    ) -> None:
        '''This saves the dataframe as a CSV using the layout written and expected by Spark/Hadoop.

        E.g. if the given storage maps the asset's path to the filesystem path "/a/b/c", a directory
        will be created with two files inside it:

            /a/b/c/
                part-00000.csv
                _SUCCESS
        '''
        directory = storage.get_fs_path(path)
        os.makedirs(directory, exist_ok=True)
        open(os.path.join(directory, '_SUCCESS'), 'wb').close()
        csv_path = os.path.join(directory, 'part-00000.csv')
        obj.to_csv(csv_path)

    @classmethod
    def load(cls, storage: LocalFileSystemStorage, path: Tuple[str, ...], _resources):
        '''This reads a dataframe from a CSV using the layout written and expected by Spark/Hadoop.

        E.g. if the given storage maps the asset's path to the filesystem path "/a/b/c", and that
        directory contains:

            /a/b/c/
                part-00000.csv
                part-00001.csv
                _SUCCESS

        then the produced dataframe will contain the concatenated contents of the two CSV files.
        '''
        paths = glob.glob(os.path.join(storage.get_fs_path(path), '*.csv'))
        return pd.concat(map(pd.read_csv, paths))


class SparkDFLocalFileSystemPolicy(TypeStoragePolicy):
    @classmethod
    def in_memory_type(cls):
        return SparkDF

    @classmethod
    def storage_definition(cls):
        return local_file_system_storage

    @classmethod
    def save(cls, obj: SparkDF, storage: LocalFileSystemStorage, path: Tuple[str, ...], _resources):
        obj.write.format('csv').options(header='true').save(
            storage.get_fs_path(path), mode='overwrite'
        )

    @classmethod
    def load(cls, storage, path, resources):
        return (
            resources.pyspark.spark_session.read.format('csv')
            .options(header='true')
            .load(storage.get_fs_path(path))
        )


class PandasDFS3Policy(TypeStoragePolicy):
    @classmethod
    def in_memory_type(cls):
        return PandasDF

    @classmethod
    def storage_definition(cls):
        return s3_storage

    @classmethod
    def save(cls, obj, storage, path, _resources):
        # TODO: write to a temporary file and then boto to s3
        raise NotImplementedError()

    @classmethod
    def load(cls, storage, path, _resources):
        s3 = boto3.resource('s3', region_name=storage.region_name)
        s3_obj = s3.Object(storage.bucket, storage.get_key(path))  # pylint: disable=no-member
        return pd.read_csv(s3_obj.get()['Body'])


class SparkDFS3Policy(TypeStoragePolicy):
    @classmethod
    def in_memory_type(cls):
        return SparkDF

    @classmethod
    def storage_definition(cls):
        return s3_storage

    @classmethod
    def save(cls, obj, storage, path, _resources):
        obj.write.format('csv').options(header='true').save(
            cls._get_uri(storage, path), mode='overwrite'
        )

    @classmethod
    def load(cls, storage, path, resources):
        resources.pyspark.spark_session.read.csv(cls._get_uri(storage, path))

    @classmethod
    def _get_uri(cls, storage, path):
        return 's3://' + storage.get_path(path)


def make_simple_lakehouse():
    dev_mode = ModeDefinition(
        name='dev',
        resource_defs={'pyspark': pyspark_resource, 'filesystem': local_file_system_storage},
    )
    dev = PresetDefinition(
        name='dev',
        mode='dev',
        run_config={'resources': {'filesystem': {'config': {'root': '.'}}}},
        solid_selection=None,
    )

    prod_mode = ModeDefinition(
        name='prod', resource_defs={'pyspark': pyspark_resource, 'filesystem': s3_storage},
    )
    prod = PresetDefinition(
        name='prod',
        mode='prod',
        run_config={'resources': {'filesystem': {'config': {'root': '.'}}}},
        solid_selection=None,
    )

    return Lakehouse(
        preset_defs=[dev, prod],
        mode_defs=[dev_mode, prod_mode],
        in_memory_type_resource_keys={SparkDF: ['pyspark']},
        type_storage_policies=[
            SparkDFLocalFileSystemPolicy,
            PandasDFLocalFileSystemPolicy,
            SparkDFS3Policy,
            PandasDFS3Policy,
        ],
    )


simple_lakehouse = make_simple_lakehouse()
