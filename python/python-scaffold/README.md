python-scaffold is a script to allow for easy creation of python modules:

Example usage:

```python-scaffold example_module```

This creates a module named example_module in the folder "example_module" in the local directory.

It will have the following layout:

```
example_module/
  example_module/
    __init__.py
  example_module_tests
    __init__.py
  setup.py
```

You must change setup.py to replace <<test folder>> with example_module_tests. (This could easily be automated).

This setup assumes that you will install example_module with ```pip install -e example_module`` for local development.
Local develop mode installation makes it easy to include example_module from example_module_tests without having to do
include path manipulation or other similar wizardry.

This also deviates from most python module layouts as the tests folder is specific to the module. E.g. "example_module_tests"
instead of "tests". I was encountering some odd behavior in the pytest/vscode integration that was fixed by making every
tests folder uniquely named. This fix worked and so I moved on. I don't recall the exact bug. 

This script is definitely a bit rough and highly specific to this exact style of repo but it is useful for my purposes.
