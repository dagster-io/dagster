# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_error_resource 1'] = 'Pipeline failure during initialization of pipeline "resource_error_pipeline". This may be due to a failure in initializing a resource or logger.'
