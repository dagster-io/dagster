/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetCheckHandleInput = {
  assetKey: AssetKeyInput;
  name: string;
};

export type AssetConditionEvaluationStatus = 'FALSE' | 'SKIPPED' | 'TRUE';

export type AssetJobKeyInput = {
  jobName: string;
};

export type AssetKeyInput = {
  path: Array<string>;
};

export type AutoMaterializeDecisionType = 'DISCARD' | 'MATERIALIZE' | 'SKIP';

export type EntityKeyFragment_AssetCheckhandle = {
  __typename: 'AssetCheckhandle';
  name: string;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
};

export type EntityKeyFragment_AssetJobKey = {__typename: 'AssetJobKey'; jobName: string};

export type EntityKeyFragment_AssetKey = {__typename: 'AssetKey'; path: Array<string>};

export type EntityKeyFragment =
  | EntityKeyFragment_AssetCheckhandle
  | EntityKeyFragment_AssetJobKey
  | EntityKeyFragment_AssetKey;

export type SpecificPartitionAssetConditionEvaluationNodeFragment = {
  __typename: 'SpecificPartitionAssetConditionEvaluationNode';
  description: string;
  status: Types.AssetConditionEvaluationStatus;
  uniqueId: string;
  childUniqueIds: Array<string>;
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
  entityKey:
    | {
        __typename: 'AssetCheckhandle';
        name: string;
        assetKey: {__typename: 'AssetKey'; path: Array<string>};
      }
    | {__typename: 'AssetJobKey'; jobName: string}
    | {__typename: 'AssetKey'; path: Array<string>};
};

export type UnpartitionedAssetConditionEvaluationNodeFragment = {
  __typename: 'UnpartitionedAssetConditionEvaluationNode';
  description: string;
  startTimestamp: number | null;
  endTimestamp: number | null;
  status: Types.AssetConditionEvaluationStatus;
  uniqueId: string;
  childUniqueIds: Array<string>;
  entityKey:
    | {
        __typename: 'AssetCheckhandle';
        name: string;
        assetKey: {__typename: 'AssetKey'; path: Array<string>};
      }
    | {__typename: 'AssetJobKey'; jobName: string}
    | {__typename: 'AssetKey'; path: Array<string>};
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

export type PartitionedAssetConditionEvaluationNodeFragment = {
  __typename: 'PartitionedAssetConditionEvaluationNode';
  description: string;
  startTimestamp: number | null;
  endTimestamp: number | null;
  numTrue: number | null;
  uniqueId: string;
  childUniqueIds: Array<string>;
  numCandidates: number | null;
  entityKey:
    | {
        __typename: 'AssetCheckhandle';
        name: string;
        assetKey: {__typename: 'AssetKey'; path: Array<string>};
      }
    | {__typename: 'AssetJobKey'; jobName: string}
    | {__typename: 'AssetKey'; path: Array<string>};
};

export type SinceMetadataFragment = {
  __typename: 'SinceConditionMetadata';
  triggerEvaluationId: string | null;
  triggerTimestamp: number | null;
  resetEvaluationId: string | null;
  resetTimestamp: number | null;
};

export type NewEvaluationNodeFragment = {
  __typename: 'AutomationConditionEvaluationNode';
  uniqueId: string;
  expandedLabel: Array<string>;
  userLabel: string | null;
  startTimestamp: number | null;
  endTimestamp: number | null;
  numCandidates: number | null;
  numTrue: number | null;
  isPartitioned: boolean;
  childUniqueIds: Array<string>;
  operatorType: string;
  entityKey:
    | {
        __typename: 'AssetCheckhandle';
        name: string;
        assetKey: {__typename: 'AssetKey'; path: Array<string>};
      }
    | {__typename: 'AssetJobKey'; jobName: string}
    | {__typename: 'AssetKey'; path: Array<string>};
  sinceMetadata: {
    __typename: 'SinceConditionMetadata';
    triggerEvaluationId: string | null;
    triggerTimestamp: number | null;
    resetEvaluationId: string | null;
    resetTimestamp: number | null;
  } | null;
};

export type AssetConditionEvaluationRecordFragment = {
  __typename: 'AssetConditionEvaluationRecord';
  id: string;
  evaluationId: string;
  numRequested: number | null;
  runIds: Array<string>;
  timestamp: number;
  startTimestamp: number | null;
  endTimestamp: number | null;
  isLegacy: boolean;
  assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
  evaluation: {
    __typename: 'AssetConditionEvaluation';
    rootUniqueId: string;
    evaluationNodes: Array<
      | {
          __typename: 'PartitionedAssetConditionEvaluationNode';
          description: string;
          startTimestamp: number | null;
          endTimestamp: number | null;
          numTrue: number | null;
          uniqueId: string;
          childUniqueIds: Array<string>;
          numCandidates: number | null;
          entityKey:
            | {
                __typename: 'AssetCheckhandle';
                name: string;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {__typename: 'AssetJobKey'; jobName: string}
            | {__typename: 'AssetKey'; path: Array<string>};
        }
      | {
          __typename: 'SpecificPartitionAssetConditionEvaluationNode';
          description: string;
          status: Types.AssetConditionEvaluationStatus;
          uniqueId: string;
          childUniqueIds: Array<string>;
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
          entityKey:
            | {
                __typename: 'AssetCheckhandle';
                name: string;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {__typename: 'AssetJobKey'; jobName: string}
            | {__typename: 'AssetKey'; path: Array<string>};
        }
      | {
          __typename: 'UnpartitionedAssetConditionEvaluationNode';
          description: string;
          startTimestamp: number | null;
          endTimestamp: number | null;
          status: Types.AssetConditionEvaluationStatus;
          uniqueId: string;
          childUniqueIds: Array<string>;
          entityKey:
            | {
                __typename: 'AssetCheckhandle';
                name: string;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {__typename: 'AssetJobKey'; jobName: string}
            | {__typename: 'AssetKey'; path: Array<string>};
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
  evaluationNodes: Array<{
    __typename: 'AutomationConditionEvaluationNode';
    uniqueId: string;
    expandedLabel: Array<string>;
    userLabel: string | null;
    startTimestamp: number | null;
    endTimestamp: number | null;
    numCandidates: number | null;
    numTrue: number | null;
    isPartitioned: boolean;
    childUniqueIds: Array<string>;
    operatorType: string;
    entityKey:
      | {
          __typename: 'AssetCheckhandle';
          name: string;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
        }
      | {__typename: 'AssetJobKey'; jobName: string}
      | {__typename: 'AssetKey'; path: Array<string>};
    sinceMetadata: {
      __typename: 'SinceConditionMetadata';
      triggerEvaluationId: string | null;
      triggerTimestamp: number | null;
      resetEvaluationId: string | null;
      resetTimestamp: number | null;
    } | null;
  }>;
};

export type GetEvaluationsQueryVariables = Exact<{
  assetKey: Types.AssetKeyInput;
  assetCheckKey?: Types.AssetCheckHandleInput | null | undefined;
  limit: number;
  cursor?: string | null | undefined;
}>;

export type GetEvaluationsQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        autoMaterializePolicy: {
          __typename: 'AutoMaterializePolicy';
          rules: Array<{
            __typename: 'AutoMaterializeRule';
            description: string;
            decisionType: Types.AutoMaterializeDecisionType;
            className: string;
          }>;
        } | null;
      }
    | {__typename: 'AssetNotFoundError'};
  assetConditionEvaluationRecordsOrError:
    | {
        __typename: 'AssetConditionEvaluationRecords';
        records: Array<{
          __typename: 'AssetConditionEvaluationRecord';
          id: string;
          evaluationId: string;
          numRequested: number | null;
          runIds: Array<string>;
          timestamp: number;
          startTimestamp: number | null;
          endTimestamp: number | null;
          isLegacy: boolean;
          assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
          evaluation: {
            __typename: 'AssetConditionEvaluation';
            rootUniqueId: string;
            evaluationNodes: Array<
              | {
                  __typename: 'PartitionedAssetConditionEvaluationNode';
                  description: string;
                  startTimestamp: number | null;
                  endTimestamp: number | null;
                  numTrue: number | null;
                  uniqueId: string;
                  childUniqueIds: Array<string>;
                  numCandidates: number | null;
                  entityKey:
                    | {
                        __typename: 'AssetCheckhandle';
                        name: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }
                    | {__typename: 'AssetJobKey'; jobName: string}
                    | {__typename: 'AssetKey'; path: Array<string>};
                }
              | {
                  __typename: 'SpecificPartitionAssetConditionEvaluationNode';
                  description: string;
                  status: Types.AssetConditionEvaluationStatus;
                  uniqueId: string;
                  childUniqueIds: Array<string>;
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
                              tags: Array<{
                                __typename: 'DefinitionTag';
                                key: string;
                                value: string;
                              }>;
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
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
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
                  entityKey:
                    | {
                        __typename: 'AssetCheckhandle';
                        name: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }
                    | {__typename: 'AssetJobKey'; jobName: string}
                    | {__typename: 'AssetKey'; path: Array<string>};
                }
              | {
                  __typename: 'UnpartitionedAssetConditionEvaluationNode';
                  description: string;
                  startTimestamp: number | null;
                  endTimestamp: number | null;
                  status: Types.AssetConditionEvaluationStatus;
                  uniqueId: string;
                  childUniqueIds: Array<string>;
                  entityKey:
                    | {
                        __typename: 'AssetCheckhandle';
                        name: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }
                    | {__typename: 'AssetJobKey'; jobName: string}
                    | {__typename: 'AssetKey'; path: Array<string>};
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
                              tags: Array<{
                                __typename: 'DefinitionTag';
                                key: string;
                                value: string;
                              }>;
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
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
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
          evaluationNodes: Array<{
            __typename: 'AutomationConditionEvaluationNode';
            uniqueId: string;
            expandedLabel: Array<string>;
            userLabel: string | null;
            startTimestamp: number | null;
            endTimestamp: number | null;
            numCandidates: number | null;
            numTrue: number | null;
            isPartitioned: boolean;
            childUniqueIds: Array<string>;
            operatorType: string;
            entityKey:
              | {
                  __typename: 'AssetCheckhandle';
                  name: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }
              | {__typename: 'AssetJobKey'; jobName: string}
              | {__typename: 'AssetKey'; path: Array<string>};
            sinceMetadata: {
              __typename: 'SinceConditionMetadata';
              triggerEvaluationId: string | null;
              triggerTimestamp: number | null;
              resetEvaluationId: string | null;
              resetTimestamp: number | null;
            } | null;
          }>;
        }>;
      }
    | {__typename: 'AutoMaterializeAssetEvaluationNeedsMigrationError'; message: string}
    | null;
};

export type GetSlimEvaluationsQueryVariables = Exact<{
  assetKey?: Types.AssetKeyInput | null | undefined;
  assetCheckKey?: Types.AssetCheckHandleInput | null | undefined;
  assetJobKey?: Types.AssetJobKeyInput | null | undefined;
  limit: number;
  cursor?: string | null | undefined;
}>;

export type GetSlimEvaluationsQuery = {
  __typename: 'Query';
  assetConditionEvaluationRecordsOrError:
    | {
        __typename: 'AssetConditionEvaluationRecords';
        records: Array<{
          __typename: 'AssetConditionEvaluationRecord';
          id: string;
          evaluationId: string;
          numRequested: number | null;
          runIds: Array<string>;
          timestamp: number;
          startTimestamp: number | null;
          endTimestamp: number | null;
          isLegacy: boolean;
          assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
          evaluation: {
            __typename: 'AssetConditionEvaluation';
            rootUniqueId: string;
            evaluationNodes: Array<
              | {
                  __typename: 'PartitionedAssetConditionEvaluationNode';
                  description: string;
                  startTimestamp: number | null;
                  endTimestamp: number | null;
                  numTrue: number | null;
                  uniqueId: string;
                  childUniqueIds: Array<string>;
                  numCandidates: number | null;
                  entityKey:
                    | {
                        __typename: 'AssetCheckhandle';
                        name: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }
                    | {__typename: 'AssetJobKey'; jobName: string}
                    | {__typename: 'AssetKey'; path: Array<string>};
                }
              | {
                  __typename: 'SpecificPartitionAssetConditionEvaluationNode';
                  description: string;
                  status: Types.AssetConditionEvaluationStatus;
                  uniqueId: string;
                  childUniqueIds: Array<string>;
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
                              tags: Array<{
                                __typename: 'DefinitionTag';
                                key: string;
                                value: string;
                              }>;
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
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
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
                  entityKey:
                    | {
                        __typename: 'AssetCheckhandle';
                        name: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }
                    | {__typename: 'AssetJobKey'; jobName: string}
                    | {__typename: 'AssetKey'; path: Array<string>};
                }
              | {
                  __typename: 'UnpartitionedAssetConditionEvaluationNode';
                  description: string;
                  startTimestamp: number | null;
                  endTimestamp: number | null;
                  status: Types.AssetConditionEvaluationStatus;
                  uniqueId: string;
                  childUniqueIds: Array<string>;
                  entityKey:
                    | {
                        __typename: 'AssetCheckhandle';
                        name: string;
                        assetKey: {__typename: 'AssetKey'; path: Array<string>};
                      }
                    | {__typename: 'AssetJobKey'; jobName: string}
                    | {__typename: 'AssetKey'; path: Array<string>};
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
                              tags: Array<{
                                __typename: 'DefinitionTag';
                                key: string;
                                value: string;
                              }>;
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
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
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
          evaluationNodes: Array<{
            __typename: 'AutomationConditionEvaluationNode';
            uniqueId: string;
            expandedLabel: Array<string>;
            userLabel: string | null;
            startTimestamp: number | null;
            endTimestamp: number | null;
            numCandidates: number | null;
            numTrue: number | null;
            isPartitioned: boolean;
            childUniqueIds: Array<string>;
            operatorType: string;
            entityKey:
              | {
                  __typename: 'AssetCheckhandle';
                  name: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }
              | {__typename: 'AssetJobKey'; jobName: string}
              | {__typename: 'AssetKey'; path: Array<string>};
            sinceMetadata: {
              __typename: 'SinceConditionMetadata';
              triggerEvaluationId: string | null;
              triggerTimestamp: number | null;
              resetEvaluationId: string | null;
              resetTimestamp: number | null;
            } | null;
          }>;
        }>;
      }
    | {__typename: 'AutoMaterializeAssetEvaluationNeedsMigrationError'; message: string}
    | null;
};

export type GetEvaluationsSpecificPartitionQueryVariables = Exact<{
  assetKey: Types.AssetKeyInput;
  evaluationId: string;
  partition: string;
}>;

export type GetEvaluationsSpecificPartitionQuery = {
  __typename: 'Query';
  assetConditionEvaluationForPartition: {
    __typename: 'AssetConditionEvaluation';
    rootUniqueId: string;
    evaluationNodes: Array<
      | {
          __typename: 'PartitionedAssetConditionEvaluationNode';
          description: string;
          startTimestamp: number | null;
          endTimestamp: number | null;
          numTrue: number | null;
          uniqueId: string;
          childUniqueIds: Array<string>;
          numCandidates: number | null;
          entityKey:
            | {
                __typename: 'AssetCheckhandle';
                name: string;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {__typename: 'AssetJobKey'; jobName: string}
            | {__typename: 'AssetKey'; path: Array<string>};
        }
      | {
          __typename: 'SpecificPartitionAssetConditionEvaluationNode';
          description: string;
          status: Types.AssetConditionEvaluationStatus;
          uniqueId: string;
          childUniqueIds: Array<string>;
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
          entityKey:
            | {
                __typename: 'AssetCheckhandle';
                name: string;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {__typename: 'AssetJobKey'; jobName: string}
            | {__typename: 'AssetKey'; path: Array<string>};
        }
      | {
          __typename: 'UnpartitionedAssetConditionEvaluationNode';
          description: string;
          startTimestamp: number | null;
          endTimestamp: number | null;
          status: Types.AssetConditionEvaluationStatus;
          uniqueId: string;
          childUniqueIds: Array<string>;
          entityKey:
            | {
                __typename: 'AssetCheckhandle';
                name: string;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {__typename: 'AssetJobKey'; jobName: string}
            | {__typename: 'AssetKey'; path: Array<string>};
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
  } | null;
};

export type AssetLastEvaluationFragment = {
  __typename: 'AutoMaterializeAssetEvaluationRecord';
  id: string;
  evaluationId: string;
  timestamp: number;
};

export type GetAssetEvaluationDetailsQueryVariables = Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
  asOfEvaluationId: string;
}>;

export type GetAssetEvaluationDetailsQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    lastAutoMaterializationEvaluationRecord: {
      __typename: 'AutoMaterializeAssetEvaluationRecord';
      id: string;
      evaluationId: string;
      timestamp: number;
    } | null;
  }>;
};

export const GetEvaluationsQueryVersion = 'e084d699d592af22b704cbe90510c8c9f191d81d21998c051e91b6ef75db1b74';

export const GetSlimEvaluationsQueryVersion = 'c309f47ccd22619a0252dfa3a51cbd4925724e24f5cc2275f55dae147f030d79';

export const GetEvaluationsSpecificPartitionQueryVersion = 'a3f5aea29ec1f1c9c643904824dbf6a1b6e1d3412c83add89d950c94624ebf0f';

export const GetAssetEvaluationDetailsQueryVersion = 'd4538f5b4ae52ff2694f9ad6cb6e18fa265e4448107185fbc0601054064c9633';
