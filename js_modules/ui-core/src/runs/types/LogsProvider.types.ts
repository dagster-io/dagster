/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DagsterEventType =
  | 'ALERT_FAILURE'
  | 'ALERT_START'
  | 'ALERT_SUCCESS'
  | 'ASSET_CHECK_EVALUATION'
  | 'ASSET_CHECK_EVALUATION_PLANNED'
  | 'ASSET_FAILED_TO_MATERIALIZE'
  | 'ASSET_HEALTH_CHANGED'
  | 'ASSET_MATERIALIZATION'
  | 'ASSET_MATERIALIZATION_PLANNED'
  | 'ASSET_OBSERVATION'
  | 'ASSET_STORE_OPERATION'
  | 'ASSET_WIPED'
  | 'CODE_LOCATION_UPDATED'
  | 'ENGINE_EVENT'
  | 'FRESHNESS_STATE_CHANGE'
  | 'FRESHNESS_STATE_EVALUATION'
  | 'HANDLED_OUTPUT'
  | 'HOOK_COMPLETED'
  | 'HOOK_ERRORED'
  | 'HOOK_SKIPPED'
  | 'LOADED_INPUT'
  | 'LOGS_CAPTURED'
  | 'OBJECT_STORE_OPERATION'
  | 'PIPELINE_CANCELED'
  | 'PIPELINE_CANCELING'
  | 'PIPELINE_DEQUEUED'
  | 'PIPELINE_ENQUEUED'
  | 'PIPELINE_FAILURE'
  | 'PIPELINE_START'
  | 'PIPELINE_STARTING'
  | 'PIPELINE_SUCCESS'
  | 'RESOURCE_INIT_FAILURE'
  | 'RESOURCE_INIT_STARTED'
  | 'RESOURCE_INIT_SUCCESS'
  | 'RUN_CANCELED'
  | 'RUN_CANCELING'
  | 'RUN_DEQUEUED'
  | 'RUN_ENQUEUED'
  | 'RUN_FAILURE'
  | 'RUN_START'
  | 'RUN_STARTING'
  | 'RUN_SUCCESS'
  | 'STEP_EXPECTATION_RESULT'
  | 'STEP_FAILURE'
  | 'STEP_INPUT'
  | 'STEP_OUTPUT'
  | 'STEP_RESTARTED'
  | 'STEP_SKIPPED'
  | 'STEP_START'
  | 'STEP_SUCCESS'
  | 'STEP_UP_FOR_RETRY'
  | 'STEP_WORKER_STARTED'
  | 'STEP_WORKER_STARTING';

export type ErrorSource = 'FRAMEWORK_ERROR' | 'INTERRUPT' | 'UNEXPECTED_ERROR' | 'USER_CODE_ERROR';

export type LogLevel = 'CRITICAL' | 'DEBUG' | 'ERROR' | 'INFO' | 'WARNING';

export type ObjectStoreOperationType = 'CP_OBJECT' | 'GET_OBJECT' | 'RM_OBJECT' | 'SET_OBJECT';

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type PipelineRunLogsSubscriptionVariables = Exact<{
  runId: string;
  cursor?: string | null | undefined;
}>;

export type PipelineRunLogsSubscription = {
  __typename: 'Subscription';
  pipelineRunLogs:
    | {
        __typename: 'PipelineRunLogsSubscriptionFailure';
        missingRunId: string | null;
        message: string;
      }
    | {
        __typename: 'PipelineRunLogsSubscriptionSuccess';
        hasMorePastEvents: boolean;
        cursor: string;
        messages: Array<
          | {
              __typename: 'AlertFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AlertStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AlertSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetCheckEvaluationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              evaluation: {
                __typename: 'AssetCheckEvaluation';
                checkName: string;
                success: boolean;
                timestamp: number;
                partition: string | null;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
                targetMaterialization: {
                  __typename: 'AssetCheckEvaluationTargetMaterializationData';
                  timestamp: number;
                } | null;
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              };
            }
          | {
              __typename: 'AssetCheckEvaluationPlannedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetMaterializationPlannedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'EngineEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'ExecutionStepFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              errorSource: Types.ErrorSource | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
              failureMetadata: {
                __typename: 'FailureMetadata';
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              } | null;
            }
          | {
              __typename: 'ExecutionStepInputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              inputName: string;
              typeCheck: {
                __typename: 'TypeCheck';
                label: string | null;
                description: string | null;
                success: boolean;
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              };
            }
          | {
              __typename: 'ExecutionStepOutputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              outputName: string;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              typeCheck: {
                __typename: 'TypeCheck';
                label: string | null;
                description: string | null;
                success: boolean;
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              };
            }
          | {
              __typename: 'ExecutionStepRestartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepSkippedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepUpForRetryEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'FailedToMaterializeEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              partition: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'HandledOutputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              outputName: string;
              managerKey: string;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
          | {
              __typename: 'HealthChangedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              partition: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'HookCompletedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'HookErroredEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'HookSkippedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LoadedInputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              inputName: string;
              managerKey: string;
              upstreamOutputName: string | null;
              upstreamStepKey: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
          | {
              __typename: 'LogMessageEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LogsCapturedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              fileKey: string;
              stepKeys: Array<string> | null;
              pid: number | null;
              externalStdoutUrl: string | null;
              externalStderrUrl: string | null;
              eventType: Types.DagsterEventType | null;
              externalUrl: string | null;
              shellCmd: {
                __typename: 'LogRetrievalShellCommand';
                stdout: string | null;
                stderr: string | null;
              } | null;
            }
          | {
              __typename: 'MaterializationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              partition: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'ObjectStoreOperationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              operationResult: {
                __typename: 'ObjectStoreOperationResult';
                op: Types.ObjectStoreOperationType;
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              };
            }
          | {
              __typename: 'ObservationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              partition: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'ResourceInitFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'ResourceInitStartedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
          | {
              __typename: 'ResourceInitSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
          | {
              __typename: 'RunCanceledEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'RunCancelingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunDequeuedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunEnqueuedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'RunStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunStartingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'StepExpectationResultEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              expectationResult: {
                __typename: 'ExpectationResult';
                success: boolean;
                label: string | null;
                description: string | null;
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              };
            }
          | {
              __typename: 'StepWorkerStartedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
          | {
              __typename: 'StepWorkerStartingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
        >;
      };
};

export type RunLogsSubscriptionSuccessFragment = {
  __typename: 'PipelineRunLogsSubscriptionSuccess';
  hasMorePastEvents: boolean;
  cursor: string;
  messages: Array<
    | {
        __typename: 'AlertFailureEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'AlertStartEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'AlertSuccessEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'AssetCheckEvaluationEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        evaluation: {
          __typename: 'AssetCheckEvaluation';
          checkName: string;
          success: boolean;
          timestamp: number;
          partition: string | null;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
          targetMaterialization: {
            __typename: 'AssetCheckEvaluationTargetMaterializationData';
            timestamp: number;
          } | null;
          metadataEntries: Array<
            | {
                __typename: 'AssetMetadataEntry';
                label: string;
                description: string | null;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {
                __typename: 'BoolMetadataEntry';
                boolValue: boolean | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'CodeReferencesMetadataEntry';
                label: string;
                description: string | null;
                codeReferences: Array<
                  | {
                      __typename: 'LocalFileCodeReference';
                      filePath: string;
                      lineNumber: number | null;
                      label: string | null;
                    }
                  | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                >;
              }
            | {
                __typename: 'FloatMetadataEntry';
                floatValue: number | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'IntMetadataEntry';
                intValue: number | null;
                intRepr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JobMetadataEntry';
                jobName: string;
                repositoryName: string | null;
                locationName: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JsonMetadataEntry';
                jsonString: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'MarkdownMetadataEntry';
                mdStr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'NotebookMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
            | {
                __typename: 'PathMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PipelineRunMetadataEntry';
                runId: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PoolMetadataEntry';
                pool: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PythonArtifactMetadataEntry';
                module: string;
                name: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TableColumnLineageMetadataEntry';
                label: string;
                description: string | null;
                lineage: Array<{
                  __typename: 'TableColumnLineageEntry';
                  columnName: string;
                  columnDeps: Array<{
                    __typename: 'TableColumnDep';
                    columnName: string;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }>;
                }>;
              }
            | {
                __typename: 'TableMetadataEntry';
                label: string;
                description: string | null;
                table: {
                  __typename: 'Table';
                  records: Array<string>;
                  schema: {
                    __typename: 'TableSchema';
                    columns: Array<{
                      __typename: 'TableColumn';
                      name: string;
                      description: string | null;
                      type: string;
                      tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                      constraints: {
                        __typename: 'TableColumnConstraints';
                        nullable: boolean;
                        unique: boolean;
                        other: Array<string>;
                      };
                    }>;
                    constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                  };
                };
              }
            | {
                __typename: 'TableSchemaMetadataEntry';
                label: string;
                description: string | null;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              }
            | {
                __typename: 'TextMetadataEntry';
                text: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TimestampMetadataEntry';
                timestamp: number;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'UrlMetadataEntry';
                url: string;
                label: string;
                description: string | null;
              }
          >;
        };
      }
    | {
        __typename: 'AssetCheckEvaluationPlannedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'AssetMaterializationPlannedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'EngineEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'ExecutionStepFailureEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        errorSource: Types.ErrorSource | null;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
        failureMetadata: {
          __typename: 'FailureMetadata';
          metadataEntries: Array<
            | {
                __typename: 'AssetMetadataEntry';
                label: string;
                description: string | null;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {
                __typename: 'BoolMetadataEntry';
                boolValue: boolean | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'CodeReferencesMetadataEntry';
                label: string;
                description: string | null;
                codeReferences: Array<
                  | {
                      __typename: 'LocalFileCodeReference';
                      filePath: string;
                      lineNumber: number | null;
                      label: string | null;
                    }
                  | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                >;
              }
            | {
                __typename: 'FloatMetadataEntry';
                floatValue: number | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'IntMetadataEntry';
                intValue: number | null;
                intRepr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JobMetadataEntry';
                jobName: string;
                repositoryName: string | null;
                locationName: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JsonMetadataEntry';
                jsonString: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'MarkdownMetadataEntry';
                mdStr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'NotebookMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
            | {
                __typename: 'PathMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PipelineRunMetadataEntry';
                runId: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PoolMetadataEntry';
                pool: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PythonArtifactMetadataEntry';
                module: string;
                name: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TableColumnLineageMetadataEntry';
                label: string;
                description: string | null;
                lineage: Array<{
                  __typename: 'TableColumnLineageEntry';
                  columnName: string;
                  columnDeps: Array<{
                    __typename: 'TableColumnDep';
                    columnName: string;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }>;
                }>;
              }
            | {
                __typename: 'TableMetadataEntry';
                label: string;
                description: string | null;
                table: {
                  __typename: 'Table';
                  records: Array<string>;
                  schema: {
                    __typename: 'TableSchema';
                    columns: Array<{
                      __typename: 'TableColumn';
                      name: string;
                      description: string | null;
                      type: string;
                      tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                      constraints: {
                        __typename: 'TableColumnConstraints';
                        nullable: boolean;
                        unique: boolean;
                        other: Array<string>;
                      };
                    }>;
                    constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                  };
                };
              }
            | {
                __typename: 'TableSchemaMetadataEntry';
                label: string;
                description: string | null;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              }
            | {
                __typename: 'TextMetadataEntry';
                text: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TimestampMetadataEntry';
                timestamp: number;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'UrlMetadataEntry';
                url: string;
                label: string;
                description: string | null;
              }
          >;
        } | null;
      }
    | {
        __typename: 'ExecutionStepInputEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        inputName: string;
        typeCheck: {
          __typename: 'TypeCheck';
          label: string | null;
          description: string | null;
          success: boolean;
          metadataEntries: Array<
            | {
                __typename: 'AssetMetadataEntry';
                label: string;
                description: string | null;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {
                __typename: 'BoolMetadataEntry';
                boolValue: boolean | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'CodeReferencesMetadataEntry';
                label: string;
                description: string | null;
                codeReferences: Array<
                  | {
                      __typename: 'LocalFileCodeReference';
                      filePath: string;
                      lineNumber: number | null;
                      label: string | null;
                    }
                  | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                >;
              }
            | {
                __typename: 'FloatMetadataEntry';
                floatValue: number | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'IntMetadataEntry';
                intValue: number | null;
                intRepr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JobMetadataEntry';
                jobName: string;
                repositoryName: string | null;
                locationName: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JsonMetadataEntry';
                jsonString: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'MarkdownMetadataEntry';
                mdStr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'NotebookMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
            | {
                __typename: 'PathMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PipelineRunMetadataEntry';
                runId: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PoolMetadataEntry';
                pool: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PythonArtifactMetadataEntry';
                module: string;
                name: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TableColumnLineageMetadataEntry';
                label: string;
                description: string | null;
                lineage: Array<{
                  __typename: 'TableColumnLineageEntry';
                  columnName: string;
                  columnDeps: Array<{
                    __typename: 'TableColumnDep';
                    columnName: string;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }>;
                }>;
              }
            | {
                __typename: 'TableMetadataEntry';
                label: string;
                description: string | null;
                table: {
                  __typename: 'Table';
                  records: Array<string>;
                  schema: {
                    __typename: 'TableSchema';
                    columns: Array<{
                      __typename: 'TableColumn';
                      name: string;
                      description: string | null;
                      type: string;
                      tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                      constraints: {
                        __typename: 'TableColumnConstraints';
                        nullable: boolean;
                        unique: boolean;
                        other: Array<string>;
                      };
                    }>;
                    constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                  };
                };
              }
            | {
                __typename: 'TableSchemaMetadataEntry';
                label: string;
                description: string | null;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              }
            | {
                __typename: 'TextMetadataEntry';
                text: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TimestampMetadataEntry';
                timestamp: number;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'UrlMetadataEntry';
                url: string;
                label: string;
                description: string | null;
              }
          >;
        };
      }
    | {
        __typename: 'ExecutionStepOutputEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        outputName: string;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
        typeCheck: {
          __typename: 'TypeCheck';
          label: string | null;
          description: string | null;
          success: boolean;
          metadataEntries: Array<
            | {
                __typename: 'AssetMetadataEntry';
                label: string;
                description: string | null;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {
                __typename: 'BoolMetadataEntry';
                boolValue: boolean | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'CodeReferencesMetadataEntry';
                label: string;
                description: string | null;
                codeReferences: Array<
                  | {
                      __typename: 'LocalFileCodeReference';
                      filePath: string;
                      lineNumber: number | null;
                      label: string | null;
                    }
                  | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                >;
              }
            | {
                __typename: 'FloatMetadataEntry';
                floatValue: number | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'IntMetadataEntry';
                intValue: number | null;
                intRepr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JobMetadataEntry';
                jobName: string;
                repositoryName: string | null;
                locationName: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JsonMetadataEntry';
                jsonString: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'MarkdownMetadataEntry';
                mdStr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'NotebookMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
            | {
                __typename: 'PathMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PipelineRunMetadataEntry';
                runId: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PoolMetadataEntry';
                pool: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PythonArtifactMetadataEntry';
                module: string;
                name: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TableColumnLineageMetadataEntry';
                label: string;
                description: string | null;
                lineage: Array<{
                  __typename: 'TableColumnLineageEntry';
                  columnName: string;
                  columnDeps: Array<{
                    __typename: 'TableColumnDep';
                    columnName: string;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }>;
                }>;
              }
            | {
                __typename: 'TableMetadataEntry';
                label: string;
                description: string | null;
                table: {
                  __typename: 'Table';
                  records: Array<string>;
                  schema: {
                    __typename: 'TableSchema';
                    columns: Array<{
                      __typename: 'TableColumn';
                      name: string;
                      description: string | null;
                      type: string;
                      tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                      constraints: {
                        __typename: 'TableColumnConstraints';
                        nullable: boolean;
                        unique: boolean;
                        other: Array<string>;
                      };
                    }>;
                    constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                  };
                };
              }
            | {
                __typename: 'TableSchemaMetadataEntry';
                label: string;
                description: string | null;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              }
            | {
                __typename: 'TextMetadataEntry';
                text: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TimestampMetadataEntry';
                timestamp: number;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'UrlMetadataEntry';
                url: string;
                label: string;
                description: string | null;
              }
          >;
        };
      }
    | {
        __typename: 'ExecutionStepRestartEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'ExecutionStepSkippedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'ExecutionStepStartEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'ExecutionStepSuccessEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'ExecutionStepUpForRetryEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'FailedToMaterializeEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        partition: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
        assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
      }
    | {
        __typename: 'HandledOutputEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        outputName: string;
        managerKey: string;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
      }
    | {
        __typename: 'HealthChangedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        partition: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
        assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
      }
    | {
        __typename: 'HookCompletedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'HookErroredEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'HookSkippedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'LoadedInputEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        inputName: string;
        managerKey: string;
        upstreamOutputName: string | null;
        upstreamStepKey: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
      }
    | {
        __typename: 'LogMessageEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'LogsCapturedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        fileKey: string;
        stepKeys: Array<string> | null;
        pid: number | null;
        externalStdoutUrl: string | null;
        externalStderrUrl: string | null;
        eventType: Types.DagsterEventType | null;
        externalUrl: string | null;
        shellCmd: {
          __typename: 'LogRetrievalShellCommand';
          stdout: string | null;
          stderr: string | null;
        } | null;
      }
    | {
        __typename: 'MaterializationEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        partition: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
        assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
      }
    | {
        __typename: 'ObjectStoreOperationEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        operationResult: {
          __typename: 'ObjectStoreOperationResult';
          op: Types.ObjectStoreOperationType;
          metadataEntries: Array<
            | {
                __typename: 'AssetMetadataEntry';
                label: string;
                description: string | null;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {
                __typename: 'BoolMetadataEntry';
                boolValue: boolean | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'CodeReferencesMetadataEntry';
                label: string;
                description: string | null;
                codeReferences: Array<
                  | {
                      __typename: 'LocalFileCodeReference';
                      filePath: string;
                      lineNumber: number | null;
                      label: string | null;
                    }
                  | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                >;
              }
            | {
                __typename: 'FloatMetadataEntry';
                floatValue: number | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'IntMetadataEntry';
                intValue: number | null;
                intRepr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JobMetadataEntry';
                jobName: string;
                repositoryName: string | null;
                locationName: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JsonMetadataEntry';
                jsonString: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'MarkdownMetadataEntry';
                mdStr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'NotebookMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
            | {
                __typename: 'PathMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PipelineRunMetadataEntry';
                runId: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PoolMetadataEntry';
                pool: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PythonArtifactMetadataEntry';
                module: string;
                name: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TableColumnLineageMetadataEntry';
                label: string;
                description: string | null;
                lineage: Array<{
                  __typename: 'TableColumnLineageEntry';
                  columnName: string;
                  columnDeps: Array<{
                    __typename: 'TableColumnDep';
                    columnName: string;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }>;
                }>;
              }
            | {
                __typename: 'TableMetadataEntry';
                label: string;
                description: string | null;
                table: {
                  __typename: 'Table';
                  records: Array<string>;
                  schema: {
                    __typename: 'TableSchema';
                    columns: Array<{
                      __typename: 'TableColumn';
                      name: string;
                      description: string | null;
                      type: string;
                      tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                      constraints: {
                        __typename: 'TableColumnConstraints';
                        nullable: boolean;
                        unique: boolean;
                        other: Array<string>;
                      };
                    }>;
                    constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                  };
                };
              }
            | {
                __typename: 'TableSchemaMetadataEntry';
                label: string;
                description: string | null;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              }
            | {
                __typename: 'TextMetadataEntry';
                text: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TimestampMetadataEntry';
                timestamp: number;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'UrlMetadataEntry';
                url: string;
                label: string;
                description: string | null;
              }
          >;
        };
      }
    | {
        __typename: 'ObservationEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        partition: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
        assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
      }
    | {
        __typename: 'ResourceInitFailureEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'ResourceInitStartedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
      }
    | {
        __typename: 'ResourceInitSuccessEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
      }
    | {
        __typename: 'RunCanceledEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'RunCancelingEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunDequeuedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunEnqueuedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunFailureEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'RunStartEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunStartingEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunSuccessEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'StepExpectationResultEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        expectationResult: {
          __typename: 'ExpectationResult';
          success: boolean;
          label: string | null;
          description: string | null;
          metadataEntries: Array<
            | {
                __typename: 'AssetMetadataEntry';
                label: string;
                description: string | null;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {
                __typename: 'BoolMetadataEntry';
                boolValue: boolean | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'CodeReferencesMetadataEntry';
                label: string;
                description: string | null;
                codeReferences: Array<
                  | {
                      __typename: 'LocalFileCodeReference';
                      filePath: string;
                      lineNumber: number | null;
                      label: string | null;
                    }
                  | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                >;
              }
            | {
                __typename: 'FloatMetadataEntry';
                floatValue: number | null;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'IntMetadataEntry';
                intValue: number | null;
                intRepr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JobMetadataEntry';
                jobName: string;
                repositoryName: string | null;
                locationName: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'JsonMetadataEntry';
                jsonString: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'MarkdownMetadataEntry';
                mdStr: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'NotebookMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
            | {
                __typename: 'PathMetadataEntry';
                path: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PipelineRunMetadataEntry';
                runId: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PoolMetadataEntry';
                pool: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'PythonArtifactMetadataEntry';
                module: string;
                name: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TableColumnLineageMetadataEntry';
                label: string;
                description: string | null;
                lineage: Array<{
                  __typename: 'TableColumnLineageEntry';
                  columnName: string;
                  columnDeps: Array<{
                    __typename: 'TableColumnDep';
                    columnName: string;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }>;
                }>;
              }
            | {
                __typename: 'TableMetadataEntry';
                label: string;
                description: string | null;
                table: {
                  __typename: 'Table';
                  records: Array<string>;
                  schema: {
                    __typename: 'TableSchema';
                    columns: Array<{
                      __typename: 'TableColumn';
                      name: string;
                      description: string | null;
                      type: string;
                      tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                      constraints: {
                        __typename: 'TableColumnConstraints';
                        nullable: boolean;
                        unique: boolean;
                        other: Array<string>;
                      };
                    }>;
                    constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                  };
                };
              }
            | {
                __typename: 'TableSchemaMetadataEntry';
                label: string;
                description: string | null;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              }
            | {
                __typename: 'TextMetadataEntry';
                text: string;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'TimestampMetadataEntry';
                timestamp: number;
                label: string;
                description: string | null;
              }
            | {
                __typename: 'UrlMetadataEntry';
                url: string;
                label: string;
                description: string | null;
              }
          >;
        };
      }
    | {
        __typename: 'StepWorkerStartedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
      }
    | {
        __typename: 'StepWorkerStartingEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
      }
  >;
};

export type PipelineRunLogsSubscriptionStatusFragment = {
  __typename: 'Run';
  id: string;
  status: Types.RunStatus;
  canTerminate: boolean;
};

export type RunLogsQueryVariables = Exact<{
  runId: string;
  cursor?: string | null | undefined;
  limit?: number | null | undefined;
}>;

export type RunLogsQuery = {
  __typename: 'Query';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {__typename: 'Run'; id: string; status: Types.RunStatus; canTerminate: boolean}
    | {__typename: 'RunNotFoundError'};
  logsForRun:
    | {
        __typename: 'EventConnection';
        cursor: string;
        events: Array<
          | {
              __typename: 'AlertFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AlertStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AlertSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetCheckEvaluationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              evaluation: {
                __typename: 'AssetCheckEvaluation';
                checkName: string;
                success: boolean;
                timestamp: number;
                partition: string | null;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
                targetMaterialization: {
                  __typename: 'AssetCheckEvaluationTargetMaterializationData';
                  timestamp: number;
                } | null;
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              };
            }
          | {
              __typename: 'AssetCheckEvaluationPlannedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetMaterializationPlannedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'EngineEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'ExecutionStepFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              errorSource: Types.ErrorSource | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
              failureMetadata: {
                __typename: 'FailureMetadata';
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              } | null;
            }
          | {
              __typename: 'ExecutionStepInputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              inputName: string;
              typeCheck: {
                __typename: 'TypeCheck';
                label: string | null;
                description: string | null;
                success: boolean;
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              };
            }
          | {
              __typename: 'ExecutionStepOutputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              outputName: string;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              typeCheck: {
                __typename: 'TypeCheck';
                label: string | null;
                description: string | null;
                success: boolean;
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              };
            }
          | {
              __typename: 'ExecutionStepRestartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepSkippedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepUpForRetryEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'FailedToMaterializeEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              partition: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'HandledOutputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              outputName: string;
              managerKey: string;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
          | {
              __typename: 'HealthChangedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              partition: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'HookCompletedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'HookErroredEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'HookSkippedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LoadedInputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              inputName: string;
              managerKey: string;
              upstreamOutputName: string | null;
              upstreamStepKey: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
          | {
              __typename: 'LogMessageEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LogsCapturedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              fileKey: string;
              stepKeys: Array<string> | null;
              pid: number | null;
              externalStdoutUrl: string | null;
              externalStderrUrl: string | null;
              eventType: Types.DagsterEventType | null;
              externalUrl: string | null;
              shellCmd: {
                __typename: 'LogRetrievalShellCommand';
                stdout: string | null;
                stderr: string | null;
              } | null;
            }
          | {
              __typename: 'MaterializationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              partition: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'ObjectStoreOperationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              operationResult: {
                __typename: 'ObjectStoreOperationResult';
                op: Types.ObjectStoreOperationType;
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              };
            }
          | {
              __typename: 'ObservationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              partition: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'ResourceInitFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'ResourceInitStartedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
          | {
              __typename: 'ResourceInitSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
          | {
              __typename: 'RunCanceledEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'RunCancelingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunDequeuedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunEnqueuedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'RunStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunStartingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'StepExpectationResultEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              expectationResult: {
                __typename: 'ExpectationResult';
                success: boolean;
                label: string | null;
                description: string | null;
                metadataEntries: Array<
                  | {
                      __typename: 'AssetMetadataEntry';
                      label: string;
                      description: string | null;
                      assetKey: {__typename: 'AssetKey'; path: Array<string>};
                    }
                  | {
                      __typename: 'BoolMetadataEntry';
                      boolValue: boolean | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'CodeReferencesMetadataEntry';
                      label: string;
                      description: string | null;
                      codeReferences: Array<
                        | {
                            __typename: 'LocalFileCodeReference';
                            filePath: string;
                            lineNumber: number | null;
                            label: string | null;
                          }
                        | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                      >;
                    }
                  | {
                      __typename: 'FloatMetadataEntry';
                      floatValue: number | null;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'IntMetadataEntry';
                      intValue: number | null;
                      intRepr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JobMetadataEntry';
                      jobName: string;
                      repositoryName: string | null;
                      locationName: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'JsonMetadataEntry';
                      jsonString: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'MarkdownMetadataEntry';
                      mdStr: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'NotebookMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                  | {
                      __typename: 'PathMetadataEntry';
                      path: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PipelineRunMetadataEntry';
                      runId: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PoolMetadataEntry';
                      pool: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'PythonArtifactMetadataEntry';
                      module: string;
                      name: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TableColumnLineageMetadataEntry';
                      label: string;
                      description: string | null;
                      lineage: Array<{
                        __typename: 'TableColumnLineageEntry';
                        columnName: string;
                        columnDeps: Array<{
                          __typename: 'TableColumnDep';
                          columnName: string;
                          assetKey: {__typename: 'AssetKey'; path: Array<string>};
                        }>;
                      }>;
                    }
                  | {
                      __typename: 'TableMetadataEntry';
                      label: string;
                      description: string | null;
                      table: {
                        __typename: 'Table';
                        records: Array<string>;
                        schema: {
                          __typename: 'TableSchema';
                          columns: Array<{
                            __typename: 'TableColumn';
                            name: string;
                            description: string | null;
                            type: string;
                            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                            constraints: {
                              __typename: 'TableColumnConstraints';
                              nullable: boolean;
                              unique: boolean;
                              other: Array<string>;
                            };
                          }>;
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
                        };
                      };
                    }
                  | {
                      __typename: 'TableSchemaMetadataEntry';
                      label: string;
                      description: string | null;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    }
                  | {
                      __typename: 'TextMetadataEntry';
                      text: string;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'TimestampMetadataEntry';
                      timestamp: number;
                      label: string;
                      description: string | null;
                    }
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              };
            }
          | {
              __typename: 'StepWorkerStartedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
          | {
              __typename: 'StepWorkerStartingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              metadataEntries: Array<
                | {
                    __typename: 'AssetMetadataEntry';
                    label: string;
                    description: string | null;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }
                | {
                    __typename: 'BoolMetadataEntry';
                    boolValue: boolean | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'CodeReferencesMetadataEntry';
                    label: string;
                    description: string | null;
                    codeReferences: Array<
                      | {
                          __typename: 'LocalFileCodeReference';
                          filePath: string;
                          lineNumber: number | null;
                          label: string | null;
                        }
                      | {__typename: 'UrlCodeReference'; url: string; label: string | null}
                    >;
                  }
                | {
                    __typename: 'FloatMetadataEntry';
                    floatValue: number | null;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'IntMetadataEntry';
                    intValue: number | null;
                    intRepr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JobMetadataEntry';
                    jobName: string;
                    repositoryName: string | null;
                    locationName: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'JsonMetadataEntry';
                    jsonString: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'MarkdownMetadataEntry';
                    mdStr: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'NotebookMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
                | {
                    __typename: 'PathMetadataEntry';
                    path: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PipelineRunMetadataEntry';
                    runId: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PoolMetadataEntry';
                    pool: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'PythonArtifactMetadataEntry';
                    module: string;
                    name: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TableColumnLineageMetadataEntry';
                    label: string;
                    description: string | null;
                    lineage: Array<{
                      __typename: 'TableColumnLineageEntry';
                      columnName: string;
                      columnDeps: Array<{
                        __typename: 'TableColumnDep';
                        columnName: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }>;
                    }>;
                  }
                | {
                    __typename: 'TableMetadataEntry';
                    label: string;
                    description: string | null;
                    table: {
                      __typename: 'Table';
                      records: Array<string>;
                      schema: {
                        __typename: 'TableSchema';
                        columns: Array<{
                          __typename: 'TableColumn';
                          name: string;
                          description: string | null;
                          type: string;
                          tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                          constraints: {
                            __typename: 'TableColumnConstraints';
                            nullable: boolean;
                            unique: boolean;
                            other: Array<string>;
                          };
                        }>;
                        constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                      };
                    };
                  }
                | {
                    __typename: 'TableSchemaMetadataEntry';
                    label: string;
                    description: string | null;
                    schema: {
                      __typename: 'TableSchema';
                      columns: Array<{
                        __typename: 'TableColumn';
                        name: string;
                        description: string | null;
                        type: string;
                        tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                        constraints: {
                          __typename: 'TableColumnConstraints';
                          nullable: boolean;
                          unique: boolean;
                          other: Array<string>;
                        };
                      }>;
                      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                    };
                  }
                | {
                    __typename: 'TextMetadataEntry';
                    text: string;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'TimestampMetadataEntry';
                    timestamp: number;
                    label: string;
                    description: string | null;
                  }
                | {
                    __typename: 'UrlMetadataEntry';
                    url: string;
                    label: string;
                    description: string | null;
                  }
              >;
            }
        >;
      }
    | {__typename: 'PythonError'; message: string; stack: Array<string>}
    | {__typename: 'RunNotFoundError'};
};

export const PipelineRunLogsSubscriptionVersion = '1fef76dfc3116df896a129a3e98e3071ced9a72b302b9e551dbcd5b28e7037cd';

export const RunLogsQueryVersion = 'f81b9500cc7636e8bc477dbef44c955a449171ed951c2ffabd55c00f36aea8af';
