import pytest
from lakehouse import construct_lakehouse_pipeline, pyspark_table

from dagster import DagsterInvalidDefinitionError


def test_missing_resource():

    with pytest.raises(DagsterInvalidDefinitionError):

        @pyspark_table
        def missing(_):
            pass

        construct_lakehouse_pipeline('test', lakehouse_tables=[missing], resources={})


def test_missing_context_args():

    with pytest.raises(DagsterInvalidDefinitionError):

        @pyspark_table
        def _no_context():
            pass
