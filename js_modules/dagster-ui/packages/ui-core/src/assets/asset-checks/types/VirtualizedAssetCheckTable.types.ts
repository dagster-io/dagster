// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetCheckTableFragment = {
  __typename: 'AssetCheck';
  name: string;
  description: string | null;
  canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
  executionForLatestMaterialization: {
    __typename: 'AssetCheckExecution';
    id: string;
    runId: string;
    status: Types.AssetCheckExecutionResolvedStatus;
    stepKey: string | null;
    timestamp: number;
    evaluation: {
      __typename: 'AssetCheckEvaluation';
      severity: Types.AssetCheckSeverity;
      timestamp: number;
      targetMaterialization: {
        __typename: 'AssetCheckEvaluationTargetMaterializationData';
        timestamp: number;
        runId: string;
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
            timestamp: number | null;
            label: string;
            description: string | null;
          }
        | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
      >;
    } | null;
  } | null;
};
