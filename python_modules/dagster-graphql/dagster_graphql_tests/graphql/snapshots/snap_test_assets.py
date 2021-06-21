# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestAssetAwareEventLog.test_all_asset_keys[asset_aware_instance_in_process_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'b'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'c'
                    ]
                }
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_all_asset_keys[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'b'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'c'
                    ]
                }
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_all_asset_keys[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'b'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'c'
                    ]
                }
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_asset_tags[asset_aware_instance_in_process_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                    ],
                    'materialization': {
                        'label': 'a'
                    }
                }
            }
        ],
        'tags': [
            {
                'key': 'foo',
                'value': 'FOO'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_asset_tags[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                    ],
                    'materialization': {
                        'label': 'a'
                    }
                }
            }
        ],
        'tags': [
            {
                'key': 'foo',
                'value': 'FOO'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_asset_tags[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                    ],
                    'materialization': {
                        'label': 'a'
                    }
                }
            }
        ],
        'tags': [
            {
                'key': 'foo',
                'value': 'FOO'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_lineage[asset_aware_instance_in_process_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                        {
                            'assetKey': {
                                'path': [
                                    'a'
                                ]
                            },
                            'partitions': [
                            ]
                        }
                    ],
                    'materialization': {
                        'label': 'b'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_lineage[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                        {
                            'assetKey': {
                                'path': [
                                    'a'
                                ]
                            },
                            'partitions': [
                            ]
                        }
                    ],
                    'materialization': {
                        'label': 'b'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_lineage[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                        {
                            'assetKey': {
                                'path': [
                                    'a'
                                ]
                            },
                            'partitions': [
                            ]
                        }
                    ],
                    'materialization': {
                        'label': 'b'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_materialization[asset_aware_instance_in_process_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                    ],
                    'materialization': {
                        'label': 'a'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_materialization[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                    ],
                    'materialization': {
                        'label': 'a'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_materialization[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                    ],
                    'materialization': {
                        'label': 'a'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_not_found[asset_aware_instance_in_process_env] 1'] = {
    'assetOrError': {
        '__typename': 'AssetNotFoundError'
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_not_found[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        '__typename': 'AssetNotFoundError'
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_not_found[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        '__typename': 'AssetNotFoundError'
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_lineage[asset_aware_instance_in_process_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                        {
                            'assetKey': {
                                'path': [
                                    'a'
                                ]
                            },
                            'partitions': [
                                '1'
                            ]
                        }
                    ],
                    'materialization': {
                        'label': 'b'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_lineage[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                        {
                            'assetKey': {
                                'path': [
                                    'a'
                                ]
                            },
                            'partitions': [
                                '1'
                            ]
                        }
                    ],
                    'materialization': {
                        'label': 'b'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_lineage[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                        {
                            'assetKey': {
                                'path': [
                                    'a'
                                ]
                            },
                            'partitions': [
                                '1'
                            ]
                        }
                    ],
                    'materialization': {
                        'label': 'b'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_materialization[asset_aware_instance_in_process_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'materialization': {
                        'label': 'a'
                    }
                },
                'partition': 'partition_1'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_materialization[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'materialization': {
                        'label': 'a'
                    }
                },
                'partition': 'partition_1'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_materialization[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'materialization': {
                        'label': 'a'
                    }
                },
                'partition': 'partition_1'
            }
        ]
    }
}
