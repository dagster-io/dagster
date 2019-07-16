import pytest

from dagster import Any, Dict, Enum, EnumValue, Field, List, Optional, PermissiveDict, String
from dagster.check import CheckError, ParameterCheckError
from dagster.core.types.default_applier import apply_default_values
from dagster.core.types.config import ConfigType
from dagster.core.types.field import resolve_to_config_type
from dagster.core.types.field_utils import Selector


def test_apply_default_values():
    scalar_config_type = resolve_to_config_type(String)
    assert apply_default_values(scalar_config_type, 'foo') == 'foo'
    assert apply_default_values(scalar_config_type, 3) == 3
    assert apply_default_values(scalar_config_type, {}) == {}
    assert apply_default_values(scalar_config_type, None) is None

    enum_config_type = resolve_to_config_type(
        Enum('an_enum', [EnumValue('foo'), EnumValue('bar', python_value=3)])
    )
    assert apply_default_values(enum_config_type, 'foo') == 'foo'
    assert apply_default_values(enum_config_type, 'bar') == 3
    with pytest.raises(CheckError, match='config_value should be pre-validated'):
        apply_default_values(enum_config_type, 'baz')
    with pytest.raises(CheckError, match='config_value should be pre-validated'):
        apply_default_values(enum_config_type, None)

    list_config_type = resolve_to_config_type(List[String])

    assert apply_default_values(list_config_type, ['foo']) == ['foo']
    assert apply_default_values(list_config_type, None) == []
    with pytest.raises(CheckError, match='Null list member not caught'):
        assert apply_default_values(list_config_type, [None]) == [None]

    nullable_list_config_type = resolve_to_config_type(List[Optional[String]])
    assert apply_default_values(nullable_list_config_type, ['foo']) == ['foo']
    assert apply_default_values(nullable_list_config_type, [None]) == [None]
    assert apply_default_values(nullable_list_config_type, None) == []

    composite_config_type = resolve_to_config_type(
        Dict(
            {
                'foo': Field(String),
                'bar': Field(Dict({'baz': Field(List[String])})),
                'quux': Field(String, is_optional=True, default_value='zip'),
                'quiggle': Field(String, is_optional=True),
            }
        )
    )

    with pytest.raises(CheckError, match='Missing non-optional composite member'):
        apply_default_values(composite_config_type, {})

    with pytest.raises(CheckError, match='Missing non-optional composite member'):
        apply_default_values(composite_config_type, {'bar': {'baz': ['giraffe']}, 'quux': 'nimble'})

    with pytest.raises(CheckError, match='Missing non-optional composite member'):
        apply_default_values(composite_config_type, {'foo': 'zowie', 'quux': 'nimble'})

    assert apply_default_values(
        composite_config_type, {'foo': 'zowie', 'bar': {'baz': ['giraffe']}, 'quux': 'nimble'}
    ) == {'foo': 'zowie', 'bar': {'baz': ['giraffe']}, 'quux': 'nimble'}

    assert apply_default_values(
        composite_config_type, {'foo': 'zowie', 'bar': {'baz': ['giraffe']}}
    ) == {'foo': 'zowie', 'bar': {'baz': ['giraffe']}, 'quux': 'zip'}

    assert apply_default_values(
        composite_config_type, {'foo': 'zowie', 'bar': {'baz': ['giraffe']}, 'quiggle': 'squiggle'}
    ) == {'foo': 'zowie', 'bar': {'baz': ['giraffe']}, 'quux': 'zip', 'quiggle': 'squiggle'}

    nested_composite_config_type = resolve_to_config_type(
        Dict(
            {
                'fruts': Field(
                    Dict(
                        {
                            'apple': Field(String),
                            'banana': Field(String, is_optional=True),
                            'potato': Field(String, is_optional=True, default_value='pie'),
                        }
                    )
                )
            }
        )
    )

    with pytest.raises(CheckError, match='Missing non-optional composite member'):
        apply_default_values(nested_composite_config_type, {'fruts': None})

    with pytest.raises(CheckError, match='Missing non-optional composite member'):
        apply_default_values(
            nested_composite_config_type, {'fruts': {'banana': 'good', 'potato': 'bad'}}
        )

    assert apply_default_values(
        nested_composite_config_type, {'fruts': {'apple': 'strawberry'}}
    ) == {'fruts': {'apple': 'strawberry', 'potato': 'pie'}}

    assert apply_default_values(
        nested_composite_config_type, {'fruts': {'apple': 'a', 'banana': 'b', 'potato': 'c'}}
    ) == {'fruts': {'apple': 'a', 'banana': 'b', 'potato': 'c'}}

    any_config_type = resolve_to_config_type(Any)

    assert apply_default_values(any_config_type, {'foo': 'bar'}) == {'foo': 'bar'}

    with pytest.raises(CheckError, match='Unsupported type'):
        assert apply_default_values(ConfigType('gargle', 'bargle'), 3)

    selector_config_type = resolve_to_config_type(
        Selector(
            {
                'one': Field(String),
                'another': Field(
                    Dict({'foo': Field(String, default_value='bar', is_optional=True)})
                ),
                'yet_another': Field(String, default_value='quux', is_optional=True),
            }
        )
    )

    with pytest.raises(CheckError):
        apply_default_values(selector_config_type, 'one')

    with pytest.raises(ParameterCheckError):
        apply_default_values(selector_config_type, None)

    with pytest.raises(ParameterCheckError, match='Expected dict with single item'):
        apply_default_values(selector_config_type, {})

    with pytest.raises(CheckError):
        apply_default_values(selector_config_type, {'one': 'foo', 'another': 'bar'})

    assert apply_default_values(selector_config_type, {'one': 'foo'}) == {'one': 'foo'}

    assert apply_default_values(selector_config_type, {'one': None}) == {'one': None}

    assert apply_default_values(selector_config_type, {'one': {}}) == {'one': {}}

    assert apply_default_values(selector_config_type, {'another': {}}) == {
        'another': {'foo': 'bar'}
    }

    singleton_selector_config_type = resolve_to_config_type(
        Selector({'foo': Field(String, default_value='bar', is_optional=True)})
    )

    assert apply_default_values(singleton_selector_config_type, None) == {'foo': 'bar'}

    permissive_dict_config_type = resolve_to_config_type(
        PermissiveDict(
            {'foo': Field(String), 'bar': Field(String, default_value='baz', is_optional=True)}
        )
    )

    with pytest.raises(CheckError, match='Missing non-optional composite member'):
        apply_default_values(permissive_dict_config_type, None)

    assert apply_default_values(permissive_dict_config_type, {'foo': 'wow', 'mau': 'mau'}) == {
        'foo': 'wow',
        'bar': 'baz',
        'mau': 'mau',
    }
