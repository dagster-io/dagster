'''NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT

@generated

Produced via:
parse_spark_configs.py \
	--output-file \
	../libraries/dagster-spark/dagster_spark/configs_spark.py \

'''


from dagster import Field, PermissiveDict, String


# pylint: disable=line-too-long
def spark_config():
    return Field(
        PermissiveDict(
            fields={
                'spark': Field(
                    PermissiveDict(
                        fields={
                            'app': Field(
                                PermissiveDict(
                                    fields={
                                        'name': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'driver': Field(
                                PermissiveDict(
                                    fields={
                                        'cores': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'maxResultSize': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'memory': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'memoryOverhead': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'supervise': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'extraClassPath': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'extraJavaOptions': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'extraLibraryPath': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'userClassPathFirst': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'blockManager': Field(
                                            PermissiveDict(
                                                fields={
                                                    'port': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'bindAddress': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'host': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'port': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'executor': Field(
                                PermissiveDict(
                                    fields={
                                        'memory': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'pyspark': Field(
                                            PermissiveDict(
                                                fields={
                                                    'memory': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'memoryOverhead': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'extraClassPath': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'extraJavaOptions': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'extraLibraryPath': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'logs': Field(
                                            PermissiveDict(
                                                fields={
                                                    'rolling': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'maxRetainedFiles': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                ),
                                                                'enableCompression': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                ),
                                                                'maxSize': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                ),
                                                                'strategy': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                ),
                                                                'time': Field(
                                                                    PermissiveDict(
                                                                        fields={
                                                                            'interval': Field(
                                                                                String,
                                                                                description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                                is_optional=True,
                                                                            )
                                                                        }
                                                                    )
                                                                ),
                                                            }
                                                        )
                                                    )
                                                }
                                            )
                                        ),
                                        'userClassPathFirst': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'cores': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'heartbeatInterval': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'extraListeners': Field(
                                String,
                                description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                is_optional=True,
                            ),
                            'local': Field(
                                PermissiveDict(
                                    fields={
                                        'dir': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'logConf': Field(
                                String,
                                description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                is_optional=True,
                            ),
                            'master': Field(
                                String,
                                description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                is_optional=True,
                            ),
                            'submit': Field(
                                PermissiveDict(
                                    fields={
                                        'deployMode': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'pyFiles': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'log': Field(
                                PermissiveDict(
                                    fields={
                                        'callerContext': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'redaction': Field(
                                PermissiveDict(
                                    fields={
                                        'regex': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'python': Field(
                                PermissiveDict(
                                    fields={
                                        'profile': Field(
                                            PermissiveDict(
                                                fields={
                                                    'root': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'dump': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                        'worker': Field(
                                            PermissiveDict(
                                                fields={
                                                    'memory': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'reuse': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            'files': Field(
                                PermissiveDict(
                                    fields={
                                        'root': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'fetchTimeout': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'useFetchCache': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'overwrite': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'maxPartitionBytes': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'openCostInBytes': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'jars': Field(
                                PermissiveDict(
                                    fields={
                                        'root': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'packages': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'excludes': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'ivy': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'ivySettings': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'repositories': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'pyspark': Field(
                                PermissiveDict(
                                    fields={
                                        'driver': Field(
                                            PermissiveDict(
                                                fields={
                                                    'python': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'python': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'reducer': Field(
                                PermissiveDict(
                                    fields={
                                        'maxSizeInFlight': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'maxReqsInFlight': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'maxBlocksInFlightPerAddress': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'maxRemoteBlockSizeFetchToMem': Field(
                                String,
                                description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                is_optional=True,
                            ),
                            'shuffle': Field(
                                PermissiveDict(
                                    fields={
                                        'compress': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'file': Field(
                                            PermissiveDict(
                                                fields={
                                                    'buffer': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'io': Field(
                                            PermissiveDict(
                                                fields={
                                                    'maxRetries': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'numConnectionsPerPeer': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'preferDirectBufs': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'retryWait': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                        'service': Field(
                                            PermissiveDict(
                                                fields={
                                                    'enabled': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'port': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'index': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'cache': Field(
                                                                    PermissiveDict(
                                                                        fields={
                                                                            'size': Field(
                                                                                String,
                                                                                description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                                is_optional=True,
                                                                            )
                                                                        }
                                                                    )
                                                                )
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        'maxChunksBeingTransferred': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'sort': Field(
                                            PermissiveDict(
                                                fields={
                                                    'bypassMergeThreshold': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'spill': Field(
                                            PermissiveDict(
                                                fields={
                                                    'compress': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'accurateBlockThreshold': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'registration': Field(
                                            PermissiveDict(
                                                fields={
                                                    'timeout': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'maxAttempts': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                        'memoryFraction': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'eventLog': Field(
                                PermissiveDict(
                                    fields={
                                        'logBlockUpdates': Field(
                                            PermissiveDict(
                                                fields={
                                                    'enabled': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'longForm': Field(
                                            PermissiveDict(
                                                fields={
                                                    'enabled': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'compress': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'dir': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'enabled': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'overwrite': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'buffer': Field(
                                            PermissiveDict(
                                                fields={
                                                    'kb': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            'ui': Field(
                                PermissiveDict(
                                    fields={
                                        'dagGraph': Field(
                                            PermissiveDict(
                                                fields={
                                                    'retainedRootRDDs': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'enabled': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'killEnabled': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'liveUpdate': Field(
                                            PermissiveDict(
                                                fields={
                                                    'period': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'port': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'retainedJobs': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'retainedStages': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'retainedTasks': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'reverseProxy': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'reverseProxyUrl': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'showConsoleProgress': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'retainedDeadExecutors': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'filters': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'worker': Field(
                                PermissiveDict(
                                    fields={
                                        'ui': Field(
                                            PermissiveDict(
                                                fields={
                                                    'retainedExecutors': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'retainedDrivers': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        )
                                    }
                                )
                            ),
                            'sql': Field(
                                PermissiveDict(
                                    fields={
                                        'ui': Field(
                                            PermissiveDict(
                                                fields={
                                                    'retainedExecutions': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        )
                                    }
                                )
                            ),
                            'streaming': Field(
                                PermissiveDict(
                                    fields={
                                        'ui': Field(
                                            PermissiveDict(
                                                fields={
                                                    'retainedBatches': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'backpressure': Field(
                                            PermissiveDict(
                                                fields={
                                                    'enabled': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'initialRate': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                        'blockInterval': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'receiver': Field(
                                            PermissiveDict(
                                                fields={
                                                    'maxRate': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'writeAheadLog': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'enable': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                ),
                                                                'closeFileAfterWrite': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        'unpersist': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'stopGracefullyOnShutdown': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'kafka': Field(
                                            PermissiveDict(
                                                fields={
                                                    'maxRatePerPartition': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'minRatePerPartition': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'maxRetries': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                        'driver': Field(
                                            PermissiveDict(
                                                fields={
                                                    'writeAheadLog': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'closeFileAfterWrite': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                )
                                                            }
                                                        )
                                                    )
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            'broadcast': Field(
                                PermissiveDict(
                                    fields={
                                        'compress': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'blockSize': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'checksum': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'io': Field(
                                PermissiveDict(
                                    fields={
                                        'compression': Field(
                                            PermissiveDict(
                                                fields={
                                                    'codec': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'lz4': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'blockSize': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                )
                                                            }
                                                        )
                                                    ),
                                                    'snappy': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'blockSize': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                )
                                                            }
                                                        )
                                                    ),
                                                    'zstd': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'level': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                ),
                                                                'bufferSize': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        )
                                    }
                                )
                            ),
                            'kryo': Field(
                                PermissiveDict(
                                    fields={
                                        'classesToRegister': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'referenceTracking': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'registrationRequired': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'registrator': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'unsafe': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'kryoserializer': Field(
                                PermissiveDict(
                                    fields={
                                        'buffer': Field(
                                            PermissiveDict(
                                                fields={
                                                    'root': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'max': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        )
                                    }
                                )
                            ),
                            'rdd': Field(
                                PermissiveDict(
                                    fields={
                                        'compress': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'serializer': Field(
                                PermissiveDict(
                                    fields={
                                        'root': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'objectStreamReset': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'memory': Field(
                                PermissiveDict(
                                    fields={
                                        'fraction': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'storageFraction': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'offHeap': Field(
                                            PermissiveDict(
                                                fields={
                                                    'enabled': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'size': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                        'useLegacyMode': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'storage': Field(
                                PermissiveDict(
                                    fields={
                                        'memoryFraction': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'unrollFraction': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'replication': Field(
                                            PermissiveDict(
                                                fields={
                                                    'proactive': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'memoryMapThreshold': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'cleaner': Field(
                                PermissiveDict(
                                    fields={
                                        'periodicGC': Field(
                                            PermissiveDict(
                                                fields={
                                                    'interval': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'referenceTracking': Field(
                                            PermissiveDict(
                                                fields={
                                                    'root': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'blocking': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'root': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                ),
                                                                'shuffle': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    'cleanCheckpoints': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            'default': Field(
                                PermissiveDict(
                                    fields={
                                        'parallelism': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'hadoop': Field(
                                PermissiveDict(
                                    fields={
                                        'cloneConf': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'validateOutputSpecs': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'mapreduce': Field(
                                            PermissiveDict(
                                                fields={
                                                    'fileoutputcommitter': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'algorithm': Field(
                                                                    PermissiveDict(
                                                                        fields={
                                                                            'version': Field(
                                                                                String,
                                                                                description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                                is_optional=True,
                                                                            )
                                                                        }
                                                                    )
                                                                )
                                                            }
                                                        )
                                                    )
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            'rpc': Field(
                                PermissiveDict(
                                    fields={
                                        'message': Field(
                                            PermissiveDict(
                                                fields={
                                                    'maxSize': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'numRetries': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'retry': Field(
                                            PermissiveDict(
                                                fields={
                                                    'wait': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'askTimeout': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'lookupTimeout': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'blockManager': Field(
                                PermissiveDict(
                                    fields={
                                        'port': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'network': Field(
                                PermissiveDict(
                                    fields={
                                        'timeout': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'port': Field(
                                PermissiveDict(
                                    fields={
                                        'maxRetries': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'core': Field(
                                PermissiveDict(
                                    fields={
                                        'connection': Field(
                                            PermissiveDict(
                                                fields={
                                                    'ack': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'wait': Field(
                                                                    PermissiveDict(
                                                                        fields={
                                                                            'timeout': Field(
                                                                                String,
                                                                                description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                                is_optional=True,
                                                                            )
                                                                        }
                                                                    )
                                                                )
                                                            }
                                                        )
                                                    )
                                                }
                                            )
                                        )
                                    }
                                )
                            ),
                            'cores': Field(
                                PermissiveDict(
                                    fields={
                                        'max': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'locality': Field(
                                PermissiveDict(
                                    fields={
                                        'wait': Field(
                                            PermissiveDict(
                                                fields={
                                                    'root': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'node': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'process': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'rack': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        )
                                    }
                                )
                            ),
                            'scheduler': Field(
                                PermissiveDict(
                                    fields={
                                        'maxRegisteredResourcesWaitingTime': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'minRegisteredResourcesRatio': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'mode': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'revive': Field(
                                            PermissiveDict(
                                                fields={
                                                    'interval': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'listenerbus': Field(
                                            PermissiveDict(
                                                fields={
                                                    'eventqueue': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'capacity': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                )
                                                            }
                                                        )
                                                    )
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            'blacklist': Field(
                                PermissiveDict(
                                    fields={
                                        'enabled': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'timeout': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'task': Field(
                                            PermissiveDict(
                                                fields={
                                                    'maxTaskAttemptsPerExecutor': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'maxTaskAttemptsPerNode': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                        'stage': Field(
                                            PermissiveDict(
                                                fields={
                                                    'maxFailedTasksPerExecutor': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'maxFailedExecutorsPerNode': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                        'application': Field(
                                            PermissiveDict(
                                                fields={
                                                    'maxFailedTasksPerExecutor': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'maxFailedExecutorsPerNode': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'fetchFailure': Field(
                                                        PermissiveDict(
                                                            fields={
                                                                'enabled': Field(
                                                                    String,
                                                                    description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                                    is_optional=True,
                                                                )
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        'killBlacklistedExecutors': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'speculation': Field(
                                PermissiveDict(
                                    fields={
                                        'root': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'interval': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'multiplier': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'quantile': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'task': Field(
                                PermissiveDict(
                                    fields={
                                        'cpus': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'maxFailures': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'reaper': Field(
                                            PermissiveDict(
                                                fields={
                                                    'enabled': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'pollingInterval': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'threadDump': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'killTimeout': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            'stage': Field(
                                PermissiveDict(
                                    fields={
                                        'maxConsecutiveAttempts': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        )
                                    }
                                )
                            ),
                            'dynamicAllocation': Field(
                                PermissiveDict(
                                    fields={
                                        'enabled': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'executorIdleTimeout': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'cachedExecutorIdleTimeout': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'initialExecutors': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'maxExecutors': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'minExecutors': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'executorAllocationRatio': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'schedulerBacklogTimeout': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'sustainedSchedulerBacklogTimeout': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'r': Field(
                                PermissiveDict(
                                    fields={
                                        'numRBackendThreads': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'command': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'driver': Field(
                                            PermissiveDict(
                                                fields={
                                                    'command': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'shell': Field(
                                            PermissiveDict(
                                                fields={
                                                    'command': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        ),
                                        'backendConnectionTimeout': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'heartBeatInterval': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                            'graphx': Field(
                                PermissiveDict(
                                    fields={
                                        'pregel': Field(
                                            PermissiveDict(
                                                fields={
                                                    'checkpointInterval': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    )
                                                }
                                            )
                                        )
                                    }
                                )
                            ),
                            'deploy': Field(
                                PermissiveDict(
                                    fields={
                                        'recoveryMode': Field(
                                            String,
                                            description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                            is_optional=True,
                                        ),
                                        'zookeeper': Field(
                                            PermissiveDict(
                                                fields={
                                                    'url': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                    'dir': Field(
                                                        String,
                                                        description='''Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.''',
                                                        is_optional=True,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                        }
                    )
                )
            }
        )
    )


# pylint: enable=line-too-long
