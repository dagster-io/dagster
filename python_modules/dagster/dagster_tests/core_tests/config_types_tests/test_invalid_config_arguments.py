import re

import pytest

from dagster import DagsterInvalidDefinitionError, resource, solid


def test_bad_solid_config_argument():
    error_msg = (
        '''You have passed an object 'dkjfkd' of incorrect type "str" '''
        '''in the parameter "config" of a SolidDefinition or @solid named "_bad_config" '''
        '''where a Field, dict, or type was expected'''
    )
    with pytest.raises(DagsterInvalidDefinitionError, match=re.escape(error_msg)):

        @solid(config='dkjfkd')
        def _bad_config(_):
            pass


def test_bad_solid_config_argument_nested():
    error_msg = (
        '''You have passed an object 'kdjkfjd' of incorrect type "str" in the '''
        '''parameter "config" of a SolidDefinition or @solid named "_bad_config" '''
        '''where a Field, dict, or type was expected.'''
    )
    with pytest.raises(DagsterInvalidDefinitionError, match=re.escape(error_msg)):

        @solid(config={'field': 'kdjkfjd'})
        def _bad_config(_):
            pass


def test_bad_resource_config_argument():
    error_msg = (
        '''You have passed an object 'dkjfkd' of incorrect type "str" in the '''
        '''parameter "config" of a ResourceDefinition or @resource where a Field, '''
        '''dict, or type was expected.'''
    )
    with pytest.raises(DagsterInvalidDefinitionError, match=re.escape(error_msg)):

        @resource(config='dkjfkd')
        def _bad_config(_):
            pass
