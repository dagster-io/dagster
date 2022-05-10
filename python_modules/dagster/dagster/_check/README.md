# Check

Check is a module for easy-to-use and idiomatic runtime type checking in python.

Usage:

```
from dagster import check

def some_function(should_be_int, optional_int):
  check.int_param(should_be_int, 'should_be_int')
  check.opt_int_param(optional_int, 'optional_int')

```

This is more concise than "if-then-throw" checks, enforces error messaging, and consistent exception type throwing.

It has some other useful properties as well. Default argument values for lists and dictionaries cause counterintuitive behavior
in python. You must use "None" instead of "{}" or "[]". See discussion at https://stackoverflow.com/questions/1132941/least-astonishment-and-the-mutable-default-argument.
check captures the idiomatic way to do this.

```
def another_function(optional_dict=None):
  # if optional_dict is None, it will return a unique instance of {} instead
  the_dict = check.opt_dict_param(optional_dict, 'optional_dict')

```

Although I would prefer to use mypy to do all internal type-checking, dagster will support python 2.7 through 2020 (see https://python3statement.org/)
and mypy usability is much poorer in python 2. Additionally, even with mypy dagster interacts with user code a lot, which may
or may not be type checked. In this case, any public API should have thorough type checking to clearly communicate errors to users.
