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

export type LogsRowStructuredFragment_AlertFailureEvent = {
  __typename: 'AlertFailureEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_AlertStartEvent = {
  __typename: 'AlertStartEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_AlertSuccessEvent = {
  __typename: 'AlertSuccessEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_AssetCheckEvaluationEvent = {
  __typename: 'AssetCheckEvaluationEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
      | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
      | {
          __typename: 'PipelineRunMetadataEntry';
          runId: string;
          label: string;
          description: string | null;
        }
      | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
      | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
      | {
          __typename: 'TimestampMetadataEntry';
          timestamp: number;
          label: string;
          description: string | null;
        }
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  };
};

export type LogsRowStructuredFragment_AssetCheckEvaluationPlannedEvent = {
  __typename: 'AssetCheckEvaluationPlannedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_AssetMaterializationPlannedEvent = {
  __typename: 'AssetMaterializationPlannedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_EngineEvent = {
  __typename: 'EngineEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  markerStart: string | null;
  markerEnd: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
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
};

export type LogsRowStructuredFragment_ExecutionStepFailureEvent = {
  __typename: 'ExecutionStepFailureEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
      | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
      | {
          __typename: 'PipelineRunMetadataEntry';
          runId: string;
          label: string;
          description: string | null;
        }
      | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
      | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
      | {
          __typename: 'TimestampMetadataEntry';
          timestamp: number;
          label: string;
          description: string | null;
        }
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  } | null;
};

export type LogsRowStructuredFragment_ExecutionStepInputEvent = {
  __typename: 'ExecutionStepInputEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
      | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
      | {
          __typename: 'PipelineRunMetadataEntry';
          runId: string;
          label: string;
          description: string | null;
        }
      | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
      | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
      | {
          __typename: 'TimestampMetadataEntry';
          timestamp: number;
          label: string;
          description: string | null;
        }
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  };
};

export type LogsRowStructuredFragment_ExecutionStepOutputEvent = {
  __typename: 'ExecutionStepOutputEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
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
      | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
      | {
          __typename: 'PipelineRunMetadataEntry';
          runId: string;
          label: string;
          description: string | null;
        }
      | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
      | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
      | {
          __typename: 'TimestampMetadataEntry';
          timestamp: number;
          label: string;
          description: string | null;
        }
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  };
};

export type LogsRowStructuredFragment_ExecutionStepRestartEvent = {
  __typename: 'ExecutionStepRestartEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_ExecutionStepSkippedEvent = {
  __typename: 'ExecutionStepSkippedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_ExecutionStepStartEvent = {
  __typename: 'ExecutionStepStartEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_ExecutionStepSuccessEvent = {
  __typename: 'ExecutionStepSuccessEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_ExecutionStepUpForRetryEvent = {
  __typename: 'ExecutionStepUpForRetryEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
};

export type LogsRowStructuredFragment_FailedToMaterializeEvent = {
  __typename: 'FailedToMaterializeEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
  assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
};

export type LogsRowStructuredFragment_HandledOutputEvent = {
  __typename: 'HandledOutputEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment_HealthChangedEvent = {
  __typename: 'HealthChangedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
  assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
};

export type LogsRowStructuredFragment_HookCompletedEvent = {
  __typename: 'HookCompletedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_HookErroredEvent = {
  __typename: 'HookErroredEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
};

export type LogsRowStructuredFragment_HookSkippedEvent = {
  __typename: 'HookSkippedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_LoadedInputEvent = {
  __typename: 'LoadedInputEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment_LogMessageEvent = {
  __typename: 'LogMessageEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_LogsCapturedEvent = {
  __typename: 'LogsCapturedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
  fileKey: string;
  stepKeys: Array<string> | null;
  externalUrl: string | null;
  externalStdoutUrl: string | null;
  externalStderrUrl: string | null;
  shellCmd: {
    __typename: 'LogRetrievalShellCommand';
    stdout: string | null;
    stderr: string | null;
  } | null;
};

export type LogsRowStructuredFragment_MaterializationEvent = {
  __typename: 'MaterializationEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
  assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
};

export type LogsRowStructuredFragment_ObjectStoreOperationEvent = {
  __typename: 'ObjectStoreOperationEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
      | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
      | {
          __typename: 'PipelineRunMetadataEntry';
          runId: string;
          label: string;
          description: string | null;
        }
      | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
      | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
      | {
          __typename: 'TimestampMetadataEntry';
          timestamp: number;
          label: string;
          description: string | null;
        }
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  };
};

export type LogsRowStructuredFragment_ObservationEvent = {
  __typename: 'ObservationEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
  assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
};

export type LogsRowStructuredFragment_ResourceInitFailureEvent = {
  __typename: 'ResourceInitFailureEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  markerStart: string | null;
  markerEnd: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
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
};

export type LogsRowStructuredFragment_ResourceInitStartedEvent = {
  __typename: 'ResourceInitStartedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  markerStart: string | null;
  markerEnd: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment_ResourceInitSuccessEvent = {
  __typename: 'ResourceInitSuccessEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  markerStart: string | null;
  markerEnd: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment_RunCanceledEvent = {
  __typename: 'RunCanceledEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
};

export type LogsRowStructuredFragment_RunCancelingEvent = {
  __typename: 'RunCancelingEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunDequeuedEvent = {
  __typename: 'RunDequeuedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunEnqueuedEvent = {
  __typename: 'RunEnqueuedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunFailureEvent = {
  __typename: 'RunFailureEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
};

export type LogsRowStructuredFragment_RunStartEvent = {
  __typename: 'RunStartEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunStartingEvent = {
  __typename: 'RunStartingEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunSuccessEvent = {
  __typename: 'RunSuccessEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_StepExpectationResultEvent = {
  __typename: 'StepExpectationResultEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
      | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
      | {
          __typename: 'PipelineRunMetadataEntry';
          runId: string;
          label: string;
          description: string | null;
        }
      | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
      | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
      | {
          __typename: 'TimestampMetadataEntry';
          timestamp: number;
          label: string;
          description: string | null;
        }
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  };
};

export type LogsRowStructuredFragment_StepWorkerStartedEvent = {
  __typename: 'StepWorkerStartedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  markerStart: string | null;
  markerEnd: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment_StepWorkerStartingEvent = {
  __typename: 'StepWorkerStartingEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  markerStart: string | null;
  markerEnd: string | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment =
  | LogsRowStructuredFragment_AlertFailureEvent
  | LogsRowStructuredFragment_AlertStartEvent
  | LogsRowStructuredFragment_AlertSuccessEvent
  | LogsRowStructuredFragment_AssetCheckEvaluationEvent
  | LogsRowStructuredFragment_AssetCheckEvaluationPlannedEvent
  | LogsRowStructuredFragment_AssetMaterializationPlannedEvent
  | LogsRowStructuredFragment_EngineEvent
  | LogsRowStructuredFragment_ExecutionStepFailureEvent
  | LogsRowStructuredFragment_ExecutionStepInputEvent
  | LogsRowStructuredFragment_ExecutionStepOutputEvent
  | LogsRowStructuredFragment_ExecutionStepRestartEvent
  | LogsRowStructuredFragment_ExecutionStepSkippedEvent
  | LogsRowStructuredFragment_ExecutionStepStartEvent
  | LogsRowStructuredFragment_ExecutionStepSuccessEvent
  | LogsRowStructuredFragment_ExecutionStepUpForRetryEvent
  | LogsRowStructuredFragment_FailedToMaterializeEvent
  | LogsRowStructuredFragment_HandledOutputEvent
  | LogsRowStructuredFragment_HealthChangedEvent
  | LogsRowStructuredFragment_HookCompletedEvent
  | LogsRowStructuredFragment_HookErroredEvent
  | LogsRowStructuredFragment_HookSkippedEvent
  | LogsRowStructuredFragment_LoadedInputEvent
  | LogsRowStructuredFragment_LogMessageEvent
  | LogsRowStructuredFragment_LogsCapturedEvent
  | LogsRowStructuredFragment_MaterializationEvent
  | LogsRowStructuredFragment_ObjectStoreOperationEvent
  | LogsRowStructuredFragment_ObservationEvent
  | LogsRowStructuredFragment_ResourceInitFailureEvent
  | LogsRowStructuredFragment_ResourceInitStartedEvent
  | LogsRowStructuredFragment_ResourceInitSuccessEvent
  | LogsRowStructuredFragment_RunCanceledEvent
  | LogsRowStructuredFragment_RunCancelingEvent
  | LogsRowStructuredFragment_RunDequeuedEvent
  | LogsRowStructuredFragment_RunEnqueuedEvent
  | LogsRowStructuredFragment_RunFailureEvent
  | LogsRowStructuredFragment_RunStartEvent
  | LogsRowStructuredFragment_RunStartingEvent
  | LogsRowStructuredFragment_RunSuccessEvent
  | LogsRowStructuredFragment_StepExpectationResultEvent
  | LogsRowStructuredFragment_StepWorkerStartedEvent
  | LogsRowStructuredFragment_StepWorkerStartingEvent;

export type LogsRowUnstructuredFragment_AlertFailureEvent = {
  __typename: 'AlertFailureEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_AlertStartEvent = {
  __typename: 'AlertStartEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_AlertSuccessEvent = {
  __typename: 'AlertSuccessEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_AssetCheckEvaluationEvent = {
  __typename: 'AssetCheckEvaluationEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_AssetCheckEvaluationPlannedEvent = {
  __typename: 'AssetCheckEvaluationPlannedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_AssetMaterializationPlannedEvent = {
  __typename: 'AssetMaterializationPlannedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_EngineEvent = {
  __typename: 'EngineEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepFailureEvent = {
  __typename: 'ExecutionStepFailureEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepInputEvent = {
  __typename: 'ExecutionStepInputEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepOutputEvent = {
  __typename: 'ExecutionStepOutputEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepRestartEvent = {
  __typename: 'ExecutionStepRestartEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepSkippedEvent = {
  __typename: 'ExecutionStepSkippedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepStartEvent = {
  __typename: 'ExecutionStepStartEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepSuccessEvent = {
  __typename: 'ExecutionStepSuccessEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepUpForRetryEvent = {
  __typename: 'ExecutionStepUpForRetryEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_FailedToMaterializeEvent = {
  __typename: 'FailedToMaterializeEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_HandledOutputEvent = {
  __typename: 'HandledOutputEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_HealthChangedEvent = {
  __typename: 'HealthChangedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_HookCompletedEvent = {
  __typename: 'HookCompletedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_HookErroredEvent = {
  __typename: 'HookErroredEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_HookSkippedEvent = {
  __typename: 'HookSkippedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_LoadedInputEvent = {
  __typename: 'LoadedInputEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_LogMessageEvent = {
  __typename: 'LogMessageEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_LogsCapturedEvent = {
  __typename: 'LogsCapturedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_MaterializationEvent = {
  __typename: 'MaterializationEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ObjectStoreOperationEvent = {
  __typename: 'ObjectStoreOperationEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ObservationEvent = {
  __typename: 'ObservationEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ResourceInitFailureEvent = {
  __typename: 'ResourceInitFailureEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ResourceInitStartedEvent = {
  __typename: 'ResourceInitStartedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ResourceInitSuccessEvent = {
  __typename: 'ResourceInitSuccessEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunCanceledEvent = {
  __typename: 'RunCanceledEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunCancelingEvent = {
  __typename: 'RunCancelingEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunDequeuedEvent = {
  __typename: 'RunDequeuedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunEnqueuedEvent = {
  __typename: 'RunEnqueuedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunFailureEvent = {
  __typename: 'RunFailureEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunStartEvent = {
  __typename: 'RunStartEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunStartingEvent = {
  __typename: 'RunStartingEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunSuccessEvent = {
  __typename: 'RunSuccessEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_StepExpectationResultEvent = {
  __typename: 'StepExpectationResultEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_StepWorkerStartedEvent = {
  __typename: 'StepWorkerStartedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_StepWorkerStartingEvent = {
  __typename: 'StepWorkerStartingEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment =
  | LogsRowUnstructuredFragment_AlertFailureEvent
  | LogsRowUnstructuredFragment_AlertStartEvent
  | LogsRowUnstructuredFragment_AlertSuccessEvent
  | LogsRowUnstructuredFragment_AssetCheckEvaluationEvent
  | LogsRowUnstructuredFragment_AssetCheckEvaluationPlannedEvent
  | LogsRowUnstructuredFragment_AssetMaterializationPlannedEvent
  | LogsRowUnstructuredFragment_EngineEvent
  | LogsRowUnstructuredFragment_ExecutionStepFailureEvent
  | LogsRowUnstructuredFragment_ExecutionStepInputEvent
  | LogsRowUnstructuredFragment_ExecutionStepOutputEvent
  | LogsRowUnstructuredFragment_ExecutionStepRestartEvent
  | LogsRowUnstructuredFragment_ExecutionStepSkippedEvent
  | LogsRowUnstructuredFragment_ExecutionStepStartEvent
  | LogsRowUnstructuredFragment_ExecutionStepSuccessEvent
  | LogsRowUnstructuredFragment_ExecutionStepUpForRetryEvent
  | LogsRowUnstructuredFragment_FailedToMaterializeEvent
  | LogsRowUnstructuredFragment_HandledOutputEvent
  | LogsRowUnstructuredFragment_HealthChangedEvent
  | LogsRowUnstructuredFragment_HookCompletedEvent
  | LogsRowUnstructuredFragment_HookErroredEvent
  | LogsRowUnstructuredFragment_HookSkippedEvent
  | LogsRowUnstructuredFragment_LoadedInputEvent
  | LogsRowUnstructuredFragment_LogMessageEvent
  | LogsRowUnstructuredFragment_LogsCapturedEvent
  | LogsRowUnstructuredFragment_MaterializationEvent
  | LogsRowUnstructuredFragment_ObjectStoreOperationEvent
  | LogsRowUnstructuredFragment_ObservationEvent
  | LogsRowUnstructuredFragment_ResourceInitFailureEvent
  | LogsRowUnstructuredFragment_ResourceInitStartedEvent
  | LogsRowUnstructuredFragment_ResourceInitSuccessEvent
  | LogsRowUnstructuredFragment_RunCanceledEvent
  | LogsRowUnstructuredFragment_RunCancelingEvent
  | LogsRowUnstructuredFragment_RunDequeuedEvent
  | LogsRowUnstructuredFragment_RunEnqueuedEvent
  | LogsRowUnstructuredFragment_RunFailureEvent
  | LogsRowUnstructuredFragment_RunStartEvent
  | LogsRowUnstructuredFragment_RunStartingEvent
  | LogsRowUnstructuredFragment_RunSuccessEvent
  | LogsRowUnstructuredFragment_StepExpectationResultEvent
  | LogsRowUnstructuredFragment_StepWorkerStartedEvent
  | LogsRowUnstructuredFragment_StepWorkerStartingEvent;
