---
title: Testing configurable resources
sidebar_position: 700
---

You can test the initialization of a <PyObject section="resources" module="dagster" object="ConfigurableResource"/> by constructing it manually. In most cases, the resource can be constructed directly:

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resource_testing endbefore=end_new_resource_testing dedent=4
from dagster import ConfigurableResource

class MyResource(ConfigurableResource):
    value: str

    def get_value(self) -> str:
        return self.value

def test_my_resource():
    assert MyResource(value="foo").get_value() == "foo"
```

If the resource requires other resources, you can pass them as constructor arguments:

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resource_testing_with_nesting endbefore=end_new_resource_testing_with_nesting dedent=4
from dagster import ConfigurableResource

class StringHolderResource(ConfigurableResource):
    value: str

class MyResourceRequiresAnother(ConfigurableResource):
    foo: StringHolderResource
    bar: str

def test_my_resource_with_nesting():
    string_holder = StringHolderResource(value="foo")
    resource = MyResourceRequiresAnother(foo=string_holder, bar="bar")
    assert resource.foo.value == "foo"
    assert resource.bar == "bar"
```

## Testing with resource context

In the case that a resource uses the resource initialization context, you can use the <PyObject section="resources" module="dagster" object="build_init_resource_context"/> utility alongside the `with_init_resource_context` helper on the resource class:

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resource_testing_with_context endbefore=end_new_resource_testing_with_context dedent=4
from dagster import (
    ConfigurableResource,
    build_init_resource_context,
    DagsterInstance,
)
from typing import Optional

class MyContextResource(ConfigurableResource[GitHub]):
    base_path: Optional[str] = None

    def effective_base_path(self) -> str:
        if self.base_path:
            return self.base_path
        instance = self.get_resource_context().instance
        assert instance
        return instance.storage_directory()

def test_my_context_resource():
    with DagsterInstance.ephemeral() as instance:
        context = build_init_resource_context(instance=instance)
        assert (
            MyContextResource(base_path=None)
            .with_resource_context(context)
            .effective_base_path()
            == instance.storage_directory()
        )
```
