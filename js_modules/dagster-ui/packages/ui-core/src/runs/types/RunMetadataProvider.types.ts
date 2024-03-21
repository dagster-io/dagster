// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunMetadataProviderMessageFragment_AlertFailureEvent = {
  __typename: 'AlertFailureEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_AlertStartEvent = {
  __typename: 'AlertStartEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_AlertSuccessEvent = {
  __typename: 'AlertSuccessEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_AssetCheckEvaluationEvent = {
  __typename: 'AssetCheckEvaluationEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_AssetCheckEvaluationPlannedEvent = {
  __typename: 'AssetCheckEvaluationPlannedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_AssetMaterializationPlannedEvent = {
  __typename: 'AssetMaterializationPlannedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_EngineEvent = {
  __typename: 'EngineEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepFailureEvent = {
  __typename: 'ExecutionStepFailureEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepInputEvent = {
  __typename: 'ExecutionStepInputEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepOutputEvent = {
  __typename: 'ExecutionStepOutputEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepRestartEvent = {
  __typename: 'ExecutionStepRestartEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepSkippedEvent = {
  __typename: 'ExecutionStepSkippedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepStartEvent = {
  __typename: 'ExecutionStepStartEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepSuccessEvent = {
  __typename: 'ExecutionStepSuccessEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepUpForRetryEvent = {
  __typename: 'ExecutionStepUpForRetryEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_HandledOutputEvent = {
  __typename: 'HandledOutputEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_HookCompletedEvent = {
  __typename: 'HookCompletedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_HookErroredEvent = {
  __typename: 'HookErroredEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_HookSkippedEvent = {
  __typename: 'HookSkippedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_LoadedInputEvent = {
  __typename: 'LoadedInputEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_LogMessageEvent = {
  __typename: 'LogMessageEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_LogsCapturedEvent = {
  __typename: 'LogsCapturedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  fileKey: string;
  stepKeys: Array<string> | null;
  pid: number | null;
  externalStdoutUrl: string | null;
  externalStderrUrl: string | null;
};

export type RunMetadataProviderMessageFragment_MaterializationEvent = {
  __typename: 'MaterializationEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ObjectStoreOperationEvent = {
  __typename: 'ObjectStoreOperationEvent';
  message: string;
  timestamp: string;
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

export type RunMetadataProviderMessageFragment_ObservationEvent = {
  __typename: 'ObservationEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ResourceInitFailureEvent = {
  __typename: 'ResourceInitFailureEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment_ResourceInitStartedEvent = {
  __typename: 'ResourceInitStartedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment_ResourceInitSuccessEvent = {
  __typename: 'ResourceInitSuccessEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment_RunCanceledEvent = {
  __typename: 'RunCanceledEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunCancelingEvent = {
  __typename: 'RunCancelingEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunDequeuedEvent = {
  __typename: 'RunDequeuedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunEnqueuedEvent = {
  __typename: 'RunEnqueuedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunFailureEvent = {
  __typename: 'RunFailureEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunStartEvent = {
  __typename: 'RunStartEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunStartingEvent = {
  __typename: 'RunStartingEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunSuccessEvent = {
  __typename: 'RunSuccessEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_StepExpectationResultEvent = {
  __typename: 'StepExpectationResultEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_StepWorkerStartedEvent = {
  __typename: 'StepWorkerStartedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment_StepWorkerStartingEvent = {
  __typename: 'StepWorkerStartingEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment =
  | RunMetadataProviderMessageFragment_AlertFailureEvent
  | RunMetadataProviderMessageFragment_AlertStartEvent
  | RunMetadataProviderMessageFragment_AlertSuccessEvent
  | RunMetadataProviderMessageFragment_AssetCheckEvaluationEvent
  | RunMetadataProviderMessageFragment_AssetCheckEvaluationPlannedEvent
  | RunMetadataProviderMessageFragment_AssetMaterializationPlannedEvent
  | RunMetadataProviderMessageFragment_EngineEvent
  | RunMetadataProviderMessageFragment_ExecutionStepFailureEvent
  | RunMetadataProviderMessageFragment_ExecutionStepInputEvent
  | RunMetadataProviderMessageFragment_ExecutionStepOutputEvent
  | RunMetadataProviderMessageFragment_ExecutionStepRestartEvent
  | RunMetadataProviderMessageFragment_ExecutionStepSkippedEvent
  | RunMetadataProviderMessageFragment_ExecutionStepStartEvent
  | RunMetadataProviderMessageFragment_ExecutionStepSuccessEvent
  | RunMetadataProviderMessageFragment_ExecutionStepUpForRetryEvent
  | RunMetadataProviderMessageFragment_HandledOutputEvent
  | RunMetadataProviderMessageFragment_HookCompletedEvent
  | RunMetadataProviderMessageFragment_HookErroredEvent
  | RunMetadataProviderMessageFragment_HookSkippedEvent
  | RunMetadataProviderMessageFragment_LoadedInputEvent
  | RunMetadataProviderMessageFragment_LogMessageEvent
  | RunMetadataProviderMessageFragment_LogsCapturedEvent
  | RunMetadataProviderMessageFragment_MaterializationEvent
  | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent
  | RunMetadataProviderMessageFragment_ObservationEvent
  | RunMetadataProviderMessageFragment_ResourceInitFailureEvent
  | RunMetadataProviderMessageFragment_ResourceInitStartedEvent
  | RunMetadataProviderMessageFragment_ResourceInitSuccessEvent
  | RunMetadataProviderMessageFragment_RunCanceledEvent
  | RunMetadataProviderMessageFragment_RunCancelingEvent
  | RunMetadataProviderMessageFragment_RunDequeuedEvent
  | RunMetadataProviderMessageFragment_RunEnqueuedEvent
  | RunMetadataProviderMessageFragment_RunFailureEvent
  | RunMetadataProviderMessageFragment_RunStartEvent
  | RunMetadataProviderMessageFragment_RunStartingEvent
  | RunMetadataProviderMessageFragment_RunSuccessEvent
  | RunMetadataProviderMessageFragment_StepExpectationResultEvent
  | RunMetadataProviderMessageFragment_StepWorkerStartedEvent
  | RunMetadataProviderMessageFragment_StepWorkerStartingEvent;
