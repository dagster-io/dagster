from dagster_graphql.schema import types


def test_schema_naming_invariant():
    violations = []
    for type_ in types():
        if type_.__name__ != f"Graphene{type_._meta.name}":  # pylint: disable=protected-access
            violations.append(
                (type_.__name__, f"Graphene{type_._meta.name}")  # pylint: disable=protected-access
            )
    assert not violations, violations
