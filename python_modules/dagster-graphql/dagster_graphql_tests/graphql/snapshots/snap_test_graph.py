# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestGraphs.test_basic_graphs[non_launchable_in_memory_instance_lazy_repository] 1'] = {
    'graphOrError': {
        '__typename': 'Graph',
        'name': 'composed_graph',
        'solidHandles': [
            {
                'handleID': 'simple_graph',
                'solid': {
                    'name': 'simple_graph'
                }
            },
            {
                'handleID': 'simple_graph.noop_solid',
                'solid': {
                    'name': 'noop_solid'
                }
            }
        ]
    }
}

snapshots['TestGraphs.test_basic_graphs[non_launchable_in_memory_instance_managed_grpc_env] 1'] = {
    'graphOrError': {
        '__typename': 'Graph',
        'name': 'composed_graph',
        'solidHandles': [
            {
                'handleID': 'simple_graph',
                'solid': {
                    'name': 'simple_graph'
                }
            },
            {
                'handleID': 'simple_graph.noop_solid',
                'solid': {
                    'name': 'noop_solid'
                }
            }
        ]
    }
}

snapshots['TestGraphs.test_basic_graphs[non_launchable_in_memory_instance_multi_location] 1'] = {
    'graphOrError': {
        '__typename': 'Graph',
        'name': 'composed_graph',
        'solidHandles': [
            {
                'handleID': 'simple_graph',
                'solid': {
                    'name': 'simple_graph'
                }
            },
            {
                'handleID': 'simple_graph.noop_solid',
                'solid': {
                    'name': 'noop_solid'
                }
            }
        ]
    }
}

snapshots['TestGraphs.test_basic_graphs[non_launchable_postgres_instance_lazy_repository] 1'] = {
    'graphOrError': {
        '__typename': 'Graph',
        'name': 'composed_graph',
        'solidHandles': [
            {
                'handleID': 'simple_graph',
                'solid': {
                    'name': 'simple_graph'
                }
            },
            {
                'handleID': 'simple_graph.noop_solid',
                'solid': {
                    'name': 'noop_solid'
                }
            }
        ]
    }
}

snapshots['TestGraphs.test_basic_graphs[non_launchable_postgres_instance_managed_grpc_env] 1'] = {
    'graphOrError': {
        '__typename': 'Graph',
        'name': 'composed_graph',
        'solidHandles': [
            {
                'handleID': 'simple_graph',
                'solid': {
                    'name': 'simple_graph'
                }
            },
            {
                'handleID': 'simple_graph.noop_solid',
                'solid': {
                    'name': 'noop_solid'
                }
            }
        ]
    }
}

snapshots['TestGraphs.test_basic_graphs[non_launchable_postgres_instance_multi_location] 1'] = {
    'graphOrError': {
        '__typename': 'Graph',
        'name': 'composed_graph',
        'solidHandles': [
            {
                'handleID': 'simple_graph',
                'solid': {
                    'name': 'simple_graph'
                }
            },
            {
                'handleID': 'simple_graph.noop_solid',
                'solid': {
                    'name': 'noop_solid'
                }
            }
        ]
    }
}

snapshots['TestGraphs.test_basic_graphs[non_launchable_sqlite_instance_deployed_grpc_env] 1'] = {
    'graphOrError': {
        '__typename': 'Graph',
        'name': 'composed_graph',
        'solidHandles': [
            {
                'handleID': 'simple_graph',
                'solid': {
                    'name': 'simple_graph'
                }
            },
            {
                'handleID': 'simple_graph.noop_solid',
                'solid': {
                    'name': 'noop_solid'
                }
            }
        ]
    }
}

snapshots['TestGraphs.test_basic_graphs[non_launchable_sqlite_instance_lazy_repository] 1'] = {
    'graphOrError': {
        '__typename': 'Graph',
        'name': 'composed_graph',
        'solidHandles': [
            {
                'handleID': 'simple_graph',
                'solid': {
                    'name': 'simple_graph'
                }
            },
            {
                'handleID': 'simple_graph.noop_solid',
                'solid': {
                    'name': 'noop_solid'
                }
            }
        ]
    }
}

snapshots['TestGraphs.test_basic_graphs[non_launchable_sqlite_instance_managed_grpc_env] 1'] = {
    'graphOrError': {
        '__typename': 'Graph',
        'name': 'composed_graph',
        'solidHandles': [
            {
                'handleID': 'simple_graph',
                'solid': {
                    'name': 'simple_graph'
                }
            },
            {
                'handleID': 'simple_graph.noop_solid',
                'solid': {
                    'name': 'noop_solid'
                }
            }
        ]
    }
}

snapshots['TestGraphs.test_basic_graphs[non_launchable_sqlite_instance_multi_location] 1'] = {
    'graphOrError': {
        '__typename': 'Graph',
        'name': 'composed_graph',
        'solidHandles': [
            {
                'handleID': 'simple_graph',
                'solid': {
                    'name': 'simple_graph'
                }
            },
            {
                'handleID': 'simple_graph.noop_solid',
                'solid': {
                    'name': 'noop_solid'
                }
            }
        ]
    }
}
