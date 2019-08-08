import pytest

from dagster import DagsterInvalidDefinitionError

from lakehouse import construct_lakehouse_pipeline, pyspark_table


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
