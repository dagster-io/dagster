// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetCheckTableFragment = {
  __typename: 'AssetCheck';
  name: string;
  description: string | null;
  canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
  blocking: boolean;
  jobNames: Array<string>;
  automationCondition: {
    __typename: 'AutomationCondition';
    label: string | null;
    expandedLabel: Array<string>;
  } | null;
  executionForLatestMaterialization: {
    __typename: 'AssetCheckExecution';
    id: string;
    runId: string;
    status: Types.AssetCheckExecutionResolvedStatus;
    stepKey: string | null;
    timestamp: number;
    run: {__typename: 'Run'; id: string; status: Types.RunStatus} | null;
    evaluation: {
      __typename: 'AssetCheckEvaluation';
      severity: Types.AssetCheckSeverity;
      timestamp: number;
      description: string | null;
      partition: string | null;
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
  } | null;
  partitionDefinition: {
    __typename: 'PartitionDefinition';
    name: string | null;
    description: string;
  } | null;
  partitionStatuses:
    | {
        __typename: 'AssetCheckDefaultPartitionStatuses';
        succeededPartitions: Array<string>;
        failedPartitions: Array<string>;
        inProgressPartitions: Array<string>;
        skippedPartitions: Array<string>;
        executionFailedPartitions: Array<string>;
      }
    | {
        __typename: 'AssetCheckMultiPartitionStatuses';
        primaryDimensionName: string;
        ranges: Array<{
          __typename: 'AssetCheckMultiPartitionRangeStatuses';
          primaryDimStartKey: string;
          primaryDimEndKey: string;
          secondaryDim:
            | {
                __typename: 'AssetCheckDefaultPartitionStatuses';
                succeededPartitions: Array<string>;
                failedPartitions: Array<string>;
                inProgressPartitions: Array<string>;
                skippedPartitions: Array<string>;
                executionFailedPartitions: Array<string>;
              }
            | {
                __typename: 'AssetCheckTimePartitionStatuses';
                ranges: Array<{
                  __typename: 'AssetCheckTimePartitionRangeStatus';
                  startKey: string;
                  endKey: string;
                  status: Types.AssetCheckPartitionRangeStatus;
                }>;
              };
        }>;
      }
    | {
        __typename: 'AssetCheckTimePartitionStatuses';
        ranges: Array<{
          __typename: 'AssetCheckTimePartitionRangeStatus';
          startKey: string;
          endKey: string;
          status: Types.AssetCheckPartitionRangeStatus;
        }>;
      }
    | null;
};
