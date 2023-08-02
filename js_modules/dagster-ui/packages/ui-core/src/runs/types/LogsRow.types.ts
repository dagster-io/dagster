// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LogsRowStructuredFragment_AlertFailureEvent_ = {
  __typename: 'AlertFailureEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_AlertStartEvent_ = {
  __typename: 'AlertStartEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_AlertSuccessEvent_ = {
  __typename: 'AlertSuccessEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_AssetMaterializationPlannedEvent_ = {
  __typename: 'AssetMaterializationPlannedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_EngineEvent_ = {
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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

export type LogsRowStructuredFragment_ExecutionStepFailureEvent_ = {
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
      | {
          __typename: 'PythonArtifactMetadataEntry';
          module: string;
          name: string;
          label: string;
          description: string | null;
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
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  } | null;
};

export type LogsRowStructuredFragment_ExecutionStepInputEvent_ = {
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
      | {
          __typename: 'PythonArtifactMetadataEntry';
          module: string;
          name: string;
          label: string;
          description: string | null;
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
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  };
};

export type LogsRowStructuredFragment_ExecutionStepOutputEvent_ = {
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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
      | {
          __typename: 'PythonArtifactMetadataEntry';
          module: string;
          name: string;
          label: string;
          description: string | null;
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
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  };
};

export type LogsRowStructuredFragment_ExecutionStepRestartEvent_ = {
  __typename: 'ExecutionStepRestartEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_ExecutionStepSkippedEvent_ = {
  __typename: 'ExecutionStepSkippedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_ExecutionStepStartEvent_ = {
  __typename: 'ExecutionStepStartEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_ExecutionStepSuccessEvent_ = {
  __typename: 'ExecutionStepSuccessEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_ExecutionStepUpForRetryEvent_ = {
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

export type LogsRowStructuredFragment_HandledOutputEvent_ = {
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment_HookCompletedEvent_ = {
  __typename: 'HookCompletedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_HookErroredEvent_ = {
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

export type LogsRowStructuredFragment_HookSkippedEvent_ = {
  __typename: 'HookSkippedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_LoadedInputEvent_ = {
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment_LogMessageEvent_ = {
  __typename: 'LogMessageEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_LogsCapturedEvent_ = {
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
};

export type LogsRowStructuredFragment_MaterializationEvent_ = {
  __typename: 'MaterializationEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
  assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
};

export type LogsRowStructuredFragment_ObjectStoreOperationEvent_ = {
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
      | {
          __typename: 'PythonArtifactMetadataEntry';
          module: string;
          name: string;
          label: string;
          description: string | null;
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
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  };
};

export type LogsRowStructuredFragment_ObservationEvent_ = {
  __typename: 'ObservationEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
  assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
};

export type LogsRowStructuredFragment_ResourceInitFailureEvent_ = {
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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

export type LogsRowStructuredFragment_ResourceInitStartedEvent_ = {
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment_ResourceInitSuccessEvent_ = {
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment_RunCanceledEvent_ = {
  __typename: 'RunCanceledEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunCancelingEvent_ = {
  __typename: 'RunCancelingEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunDequeuedEvent_ = {
  __typename: 'RunDequeuedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunEnqueuedEvent_ = {
  __typename: 'RunEnqueuedEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunFailureEvent_ = {
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

export type LogsRowStructuredFragment_RunStartEvent_ = {
  __typename: 'RunStartEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunStartingEvent_ = {
  __typename: 'RunStartingEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_RunSuccessEvent_ = {
  __typename: 'RunSuccessEvent';
  message: string;
  eventType: Types.DagsterEventType | null;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowStructuredFragment_StepExpectationResultEvent_ = {
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
      | {
          __typename: 'PythonArtifactMetadataEntry';
          module: string;
          name: string;
          label: string;
          description: string | null;
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
      | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
    >;
  };
};

export type LogsRowStructuredFragment_StepWorkerStartedEvent_ = {
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment_StepWorkerStartingEvent_ = {
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
    | {
        __typename: 'PythonArtifactMetadataEntry';
        module: string;
        name: string;
        label: string;
        description: string | null;
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
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type LogsRowStructuredFragment =
  | LogsRowStructuredFragment_AlertFailureEvent_
  | LogsRowStructuredFragment_AlertStartEvent_
  | LogsRowStructuredFragment_AlertSuccessEvent_
  | LogsRowStructuredFragment_AssetMaterializationPlannedEvent_
  | LogsRowStructuredFragment_EngineEvent_
  | LogsRowStructuredFragment_ExecutionStepFailureEvent_
  | LogsRowStructuredFragment_ExecutionStepInputEvent_
  | LogsRowStructuredFragment_ExecutionStepOutputEvent_
  | LogsRowStructuredFragment_ExecutionStepRestartEvent_
  | LogsRowStructuredFragment_ExecutionStepSkippedEvent_
  | LogsRowStructuredFragment_ExecutionStepStartEvent_
  | LogsRowStructuredFragment_ExecutionStepSuccessEvent_
  | LogsRowStructuredFragment_ExecutionStepUpForRetryEvent_
  | LogsRowStructuredFragment_HandledOutputEvent_
  | LogsRowStructuredFragment_HookCompletedEvent_
  | LogsRowStructuredFragment_HookErroredEvent_
  | LogsRowStructuredFragment_HookSkippedEvent_
  | LogsRowStructuredFragment_LoadedInputEvent_
  | LogsRowStructuredFragment_LogMessageEvent_
  | LogsRowStructuredFragment_LogsCapturedEvent_
  | LogsRowStructuredFragment_MaterializationEvent_
  | LogsRowStructuredFragment_ObjectStoreOperationEvent_
  | LogsRowStructuredFragment_ObservationEvent_
  | LogsRowStructuredFragment_ResourceInitFailureEvent_
  | LogsRowStructuredFragment_ResourceInitStartedEvent_
  | LogsRowStructuredFragment_ResourceInitSuccessEvent_
  | LogsRowStructuredFragment_RunCanceledEvent_
  | LogsRowStructuredFragment_RunCancelingEvent_
  | LogsRowStructuredFragment_RunDequeuedEvent_
  | LogsRowStructuredFragment_RunEnqueuedEvent_
  | LogsRowStructuredFragment_RunFailureEvent_
  | LogsRowStructuredFragment_RunStartEvent_
  | LogsRowStructuredFragment_RunStartingEvent_
  | LogsRowStructuredFragment_RunSuccessEvent_
  | LogsRowStructuredFragment_StepExpectationResultEvent_
  | LogsRowStructuredFragment_StepWorkerStartedEvent_
  | LogsRowStructuredFragment_StepWorkerStartingEvent_;

export type LogsRowUnstructuredFragment_AlertFailureEvent_ = {
  __typename: 'AlertFailureEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_AlertStartEvent_ = {
  __typename: 'AlertStartEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_AlertSuccessEvent_ = {
  __typename: 'AlertSuccessEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_AssetMaterializationPlannedEvent_ = {
  __typename: 'AssetMaterializationPlannedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_EngineEvent_ = {
  __typename: 'EngineEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepFailureEvent_ = {
  __typename: 'ExecutionStepFailureEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepInputEvent_ = {
  __typename: 'ExecutionStepInputEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepOutputEvent_ = {
  __typename: 'ExecutionStepOutputEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepRestartEvent_ = {
  __typename: 'ExecutionStepRestartEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepSkippedEvent_ = {
  __typename: 'ExecutionStepSkippedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepStartEvent_ = {
  __typename: 'ExecutionStepStartEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepSuccessEvent_ = {
  __typename: 'ExecutionStepSuccessEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ExecutionStepUpForRetryEvent_ = {
  __typename: 'ExecutionStepUpForRetryEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_HandledOutputEvent_ = {
  __typename: 'HandledOutputEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_HookCompletedEvent_ = {
  __typename: 'HookCompletedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_HookErroredEvent_ = {
  __typename: 'HookErroredEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_HookSkippedEvent_ = {
  __typename: 'HookSkippedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_LoadedInputEvent_ = {
  __typename: 'LoadedInputEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_LogMessageEvent_ = {
  __typename: 'LogMessageEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_LogsCapturedEvent_ = {
  __typename: 'LogsCapturedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_MaterializationEvent_ = {
  __typename: 'MaterializationEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ObjectStoreOperationEvent_ = {
  __typename: 'ObjectStoreOperationEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ObservationEvent_ = {
  __typename: 'ObservationEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ResourceInitFailureEvent_ = {
  __typename: 'ResourceInitFailureEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ResourceInitStartedEvent_ = {
  __typename: 'ResourceInitStartedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_ResourceInitSuccessEvent_ = {
  __typename: 'ResourceInitSuccessEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunCanceledEvent_ = {
  __typename: 'RunCanceledEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunCancelingEvent_ = {
  __typename: 'RunCancelingEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunDequeuedEvent_ = {
  __typename: 'RunDequeuedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunEnqueuedEvent_ = {
  __typename: 'RunEnqueuedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunFailureEvent_ = {
  __typename: 'RunFailureEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunStartEvent_ = {
  __typename: 'RunStartEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunStartingEvent_ = {
  __typename: 'RunStartingEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_RunSuccessEvent_ = {
  __typename: 'RunSuccessEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_StepExpectationResultEvent_ = {
  __typename: 'StepExpectationResultEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_StepWorkerStartedEvent_ = {
  __typename: 'StepWorkerStartedEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment_StepWorkerStartingEvent_ = {
  __typename: 'StepWorkerStartingEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
  stepKey: string | null;
};

export type LogsRowUnstructuredFragment =
  | LogsRowUnstructuredFragment_AlertFailureEvent_
  | LogsRowUnstructuredFragment_AlertStartEvent_
  | LogsRowUnstructuredFragment_AlertSuccessEvent_
  | LogsRowUnstructuredFragment_AssetMaterializationPlannedEvent_
  | LogsRowUnstructuredFragment_EngineEvent_
  | LogsRowUnstructuredFragment_ExecutionStepFailureEvent_
  | LogsRowUnstructuredFragment_ExecutionStepInputEvent_
  | LogsRowUnstructuredFragment_ExecutionStepOutputEvent_
  | LogsRowUnstructuredFragment_ExecutionStepRestartEvent_
  | LogsRowUnstructuredFragment_ExecutionStepSkippedEvent_
  | LogsRowUnstructuredFragment_ExecutionStepStartEvent_
  | LogsRowUnstructuredFragment_ExecutionStepSuccessEvent_
  | LogsRowUnstructuredFragment_ExecutionStepUpForRetryEvent_
  | LogsRowUnstructuredFragment_HandledOutputEvent_
  | LogsRowUnstructuredFragment_HookCompletedEvent_
  | LogsRowUnstructuredFragment_HookErroredEvent_
  | LogsRowUnstructuredFragment_HookSkippedEvent_
  | LogsRowUnstructuredFragment_LoadedInputEvent_
  | LogsRowUnstructuredFragment_LogMessageEvent_
  | LogsRowUnstructuredFragment_LogsCapturedEvent_
  | LogsRowUnstructuredFragment_MaterializationEvent_
  | LogsRowUnstructuredFragment_ObjectStoreOperationEvent_
  | LogsRowUnstructuredFragment_ObservationEvent_
  | LogsRowUnstructuredFragment_ResourceInitFailureEvent_
  | LogsRowUnstructuredFragment_ResourceInitStartedEvent_
  | LogsRowUnstructuredFragment_ResourceInitSuccessEvent_
  | LogsRowUnstructuredFragment_RunCanceledEvent_
  | LogsRowUnstructuredFragment_RunCancelingEvent_
  | LogsRowUnstructuredFragment_RunDequeuedEvent_
  | LogsRowUnstructuredFragment_RunEnqueuedEvent_
  | LogsRowUnstructuredFragment_RunFailureEvent_
  | LogsRowUnstructuredFragment_RunStartEvent_
  | LogsRowUnstructuredFragment_RunStartingEvent_
  | LogsRowUnstructuredFragment_RunSuccessEvent_
  | LogsRowUnstructuredFragment_StepExpectationResultEvent_
  | LogsRowUnstructuredFragment_StepWorkerStartedEvent_
  | LogsRowUnstructuredFragment_StepWorkerStartingEvent_;
