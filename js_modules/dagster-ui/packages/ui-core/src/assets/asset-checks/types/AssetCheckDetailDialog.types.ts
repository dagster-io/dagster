// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetCheckEvaluationTargetMaterializationFragment = {
  __typename: 'AssetCheckEvaluationTargetMaterializationData';
  timestamp: number;
  runId: string;
};

export type AssetCheckExecutionFragment = {
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
    description: string | null;
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

export type AssetCheckDetailsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  checkName: Types.Scalars['String']['input'];
  limit: Types.Scalars['Int']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type AssetCheckDetailsQuery = {
  __typename: 'Query';
  assetCheckExecutions: Array<{
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
      description: string | null;
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
  }>;
};

export const AssetCheckDetailsQueryVersion = 'c448858a73cd66132c2d6f232497570d217ece793897c47aaa1155b15c7ef8e9';
