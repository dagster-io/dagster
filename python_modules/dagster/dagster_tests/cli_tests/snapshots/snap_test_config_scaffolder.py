# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_basic_solids_config 1'] = {
    'execution': {
        'in_process': {
            'config': {'marker_to_close': '', 'retries': {'disabled': {}, 'enabled': {}}}
        },
        'multiprocess': {
            'config': {'max_concurrent': 0, 'retries': {'disabled': {}, 'enabled': {}}}
        },
    },
    'loggers': {'console': {'config': {'log_level': '', 'name': ''}}},
    'resources': {},
    'solids': {'required_field_solid': {'config': {'required_int': 0}}},
    'storage': {'filesystem': {'config': {'base_dir': ''}}, 'in_memory': {}},
    'intermediate_storage': {'filesystem': {'config': {'base_dir': ''}}, 'in_memory': {}},
}

snapshots['test_two_modes 1'] = {'resources': {'value': {'config': {'mode_one_field': ''}}}}

snapshots['test_two_modes 2'] = {
    'execution': {
        'in_process': {
            'config': {'marker_to_close': '', 'retries': {'disabled': {}, 'enabled': {}}}
        },
        'multiprocess': {
            'config': {'max_concurrent': 0, 'retries': {'disabled': {}, 'enabled': {}}}
        },
    },
    'loggers': {'console': {'config': {'log_level': '', 'name': ''}}},
    'resources': {'value': {'config': {'mode_one_field': ''}}},
    'solids': {},
    'storage': {'filesystem': {'config': {'base_dir': ''}}, 'in_memory': {}},
    'intermediate_storage': {'filesystem': {'config': {'base_dir': ''}}, 'in_memory': {}},
}

snapshots['test_two_modes 3'] = {'resources': {'value': {'config': {'mode_two_field': 0}}}}

snapshots['test_two_modes 4'] = {
    'execution': {
        'in_process': {
            'config': {'marker_to_close': '', 'retries': {'disabled': {}, 'enabled': {}}}
        },
        'multiprocess': {
            'config': {'max_concurrent': 0, 'retries': {'disabled': {}, 'enabled': {}}}
        },
    },
    'loggers': {'console': {'config': {'log_level': '', 'name': ''}}},
    'resources': {'value': {'config': {'mode_two_field': 0}}},
    'solids': {},
    'storage': {'filesystem': {'config': {'base_dir': ''}}, 'in_memory': {}},
    'intermediate_storage': {'filesystem': {'config': {'base_dir': ''}}, 'in_memory': {}},
}
