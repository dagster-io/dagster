from dagster.core.types.decorator import dagster_type, get_runtime_type_on_decorated_klass


def test_dagster_type_decorator():
    @dagster_type(name=None)
    class Foo(object):
        pass

    @dagster_type()
    class Bar(object):
        pass

    @dagster_type
    class Baaz(object):
        pass

    assert get_runtime_type_on_decorated_klass(Foo).name == 'Foo'
    assert get_runtime_type_on_decorated_klass(Bar).name == 'Bar'
    assert get_runtime_type_on_decorated_klass(Baaz).name == 'Baaz'
