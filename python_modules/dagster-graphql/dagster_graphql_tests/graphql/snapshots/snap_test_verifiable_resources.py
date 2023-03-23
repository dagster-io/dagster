# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_fetch_top_level_resource 1'] = {
    'topLevelResourceDetailsOrError': {
        '__typename': 'ResourceDetails',
        'description': 'My description.',
        'name': 'my_resource',
        'supportsVerification': True
    }
}

snapshots['test_fetch_top_level_resource_no_verification 1'] = {
    'topLevelResourceDetailsOrError': {
        '__typename': 'ResourceDetails',
        'description': None,
        'name': 'my_outer_resource',
        'supportsVerification': False
    }
}
