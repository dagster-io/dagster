#!/usr/bin/env python3

from dagster_module_publisher import DagsterModulePublisher  # pylint: disable=import-error

if __name__ == '__main__':
    dmp = DagsterModulePublisher()
    dmp.check_versions_equal()
    dmp.check_versions_equal(nightly=True)
