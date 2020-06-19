# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_cache_file_from_s3_step_four 1'] = {
    'file-cache-bucket': {
        'file-cache/source-file': b'foo'
    }
}
