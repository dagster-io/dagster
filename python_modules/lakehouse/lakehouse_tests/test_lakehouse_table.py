import pytest
from lakehouse import lakehouse_table, construct_lakehouse_pipeline
from dagster import DagsterInvalidDefinitionError


def test_missing_resource():

    with pytest.raises(DagsterInvalidDefinitionError):

        @lakehouse_table(required_resource_keys={'foo'})
        def missing(_):
            pass

        construct_lakehouse_pipeline('test', lakehouse_tables=[missing])


def test_missing_context_args():

    with pytest.raises(DagsterInvalidDefinitionError):

        @lakehouse_table
        def _no_context():
            pass
