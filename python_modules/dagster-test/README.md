# dagster-test

This module is used to host testing code that is used across various dagster packages. It is currently
not published to PyPI, so it should only be required by tests. Users should not install this package.

Eventually, this package will host test suites that users can import to help develop custom implementations
of various Dagster components, such as RunLaunchers, Schedulers, RunStorage, EventLogStorage, etc.
