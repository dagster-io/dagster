import uuid

import pytest

import dagstermill as dm

from dagster import (
    Field,
    SolidDefinition,
    InputDefinition,
    OutputDefinition,
    check,
    types,
)

# def test_basic_get_in_memory_input():
#     manager = dm.Manager()
#     dm_context = manager.define_context(inputs=dict(a=1))
#     assert manager.get_input(dm_context, 'a') == 1

# def test_basic_get_in_memory_inputs():
#     manager = dm.Manager()
#     dm_context = manager.define_context(inputs=(dict(a=1, b=2)))
#     assert manager.get_input(dm_context, 'a') == 1
#     assert manager.get_input(dm_context, 'b') == 2

#     a, b = manager.get_inputs(dm_context, 'a', 'b')

#     assert a == 1
#     assert b == 2
