// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunMetadataProviderMessageFragment_AlertFailureEvent_ = {
  __typename: 'AlertFailureEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_AlertStartEvent_ = {
  __typename: 'AlertStartEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_AlertSuccessEvent_ = {
  __typename: 'AlertSuccessEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_AssetMaterializationPlannedEvent_ = {
  __typename: 'AssetMaterializationPlannedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_EngineEvent_ = {
  __typename: 'EngineEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepFailureEvent_ = {
  __typename: 'ExecutionStepFailureEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepInputEvent_ = {
  __typename: 'ExecutionStepInputEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepOutputEvent_ = {
  __typename: 'ExecutionStepOutputEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepRestartEvent_ = {
  __typename: 'ExecutionStepRestartEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepSkippedEvent_ = {
  __typename: 'ExecutionStepSkippedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepStartEvent_ = {
  __typename: 'ExecutionStepStartEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepSuccessEvent_ = {
  __typename: 'ExecutionStepSuccessEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ExecutionStepUpForRetryEvent_ = {
  __typename: 'ExecutionStepUpForRetryEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_HandledOutputEvent_ = {
  __typename: 'HandledOutputEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_HookCompletedEvent_ = {
  __typename: 'HookCompletedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_HookErroredEvent_ = {
  __typename: 'HookErroredEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_HookSkippedEvent_ = {
  __typename: 'HookSkippedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_LoadedInputEvent_ = {
  __typename: 'LoadedInputEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_LogMessageEvent_ = {
  __typename: 'LogMessageEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_LogsCapturedEvent_ = {
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

export type RunMetadataProviderMessageFragment_MaterializationEvent_ = {
  __typename: 'MaterializationEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_ = {
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

export type RunMetadataProviderMessageFragment_ObservationEvent_ = {
  __typename: 'ObservationEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_ResourceInitFailureEvent_ = {
  __typename: 'ResourceInitFailureEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment_ResourceInitStartedEvent_ = {
  __typename: 'ResourceInitStartedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment_ResourceInitSuccessEvent_ = {
  __typename: 'ResourceInitSuccessEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment_RunCanceledEvent_ = {
  __typename: 'RunCanceledEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunCancelingEvent_ = {
  __typename: 'RunCancelingEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunDequeuedEvent_ = {
  __typename: 'RunDequeuedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunEnqueuedEvent_ = {
  __typename: 'RunEnqueuedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunFailureEvent_ = {
  __typename: 'RunFailureEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunStartEvent_ = {
  __typename: 'RunStartEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunStartingEvent_ = {
  __typename: 'RunStartingEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_RunSuccessEvent_ = {
  __typename: 'RunSuccessEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_StepExpectationResultEvent_ = {
  __typename: 'StepExpectationResultEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
};

export type RunMetadataProviderMessageFragment_StepWorkerStartedEvent_ = {
  __typename: 'StepWorkerStartedEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment_StepWorkerStartingEvent_ = {
  __typename: 'StepWorkerStartingEvent';
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
};

export type RunMetadataProviderMessageFragment =
  | RunMetadataProviderMessageFragment_AlertFailureEvent_
  | RunMetadataProviderMessageFragment_AlertStartEvent_
  | RunMetadataProviderMessageFragment_AlertSuccessEvent_
  | RunMetadataProviderMessageFragment_AssetMaterializationPlannedEvent_
  | RunMetadataProviderMessageFragment_EngineEvent_
  | RunMetadataProviderMessageFragment_ExecutionStepFailureEvent_
  | RunMetadataProviderMessageFragment_ExecutionStepInputEvent_
  | RunMetadataProviderMessageFragment_ExecutionStepOutputEvent_
  | RunMetadataProviderMessageFragment_ExecutionStepRestartEvent_
  | RunMetadataProviderMessageFragment_ExecutionStepSkippedEvent_
  | RunMetadataProviderMessageFragment_ExecutionStepStartEvent_
  | RunMetadataProviderMessageFragment_ExecutionStepSuccessEvent_
  | RunMetadataProviderMessageFragment_ExecutionStepUpForRetryEvent_
  | RunMetadataProviderMessageFragment_HandledOutputEvent_
  | RunMetadataProviderMessageFragment_HookCompletedEvent_
  | RunMetadataProviderMessageFragment_HookErroredEvent_
  | RunMetadataProviderMessageFragment_HookSkippedEvent_
  | RunMetadataProviderMessageFragment_LoadedInputEvent_
  | RunMetadataProviderMessageFragment_LogMessageEvent_
  | RunMetadataProviderMessageFragment_LogsCapturedEvent_
  | RunMetadataProviderMessageFragment_MaterializationEvent_
  | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_
  | RunMetadataProviderMessageFragment_ObservationEvent_
  | RunMetadataProviderMessageFragment_ResourceInitFailureEvent_
  | RunMetadataProviderMessageFragment_ResourceInitStartedEvent_
  | RunMetadataProviderMessageFragment_ResourceInitSuccessEvent_
  | RunMetadataProviderMessageFragment_RunCanceledEvent_
  | RunMetadataProviderMessageFragment_RunCancelingEvent_
  | RunMetadataProviderMessageFragment_RunDequeuedEvent_
  | RunMetadataProviderMessageFragment_RunEnqueuedEvent_
  | RunMetadataProviderMessageFragment_RunFailureEvent_
  | RunMetadataProviderMessageFragment_RunStartEvent_
  | RunMetadataProviderMessageFragment_RunStartingEvent_
  | RunMetadataProviderMessageFragment_RunSuccessEvent_
  | RunMetadataProviderMessageFragment_StepExpectationResultEvent_
  | RunMetadataProviderMessageFragment_StepWorkerStartedEvent_
  | RunMetadataProviderMessageFragment_StepWorkerStartingEvent_;
