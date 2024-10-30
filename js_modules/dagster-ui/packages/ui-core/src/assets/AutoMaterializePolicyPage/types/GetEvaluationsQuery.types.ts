// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

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

export type UnpartitionedAssetConditionEvaluationNodeFragment = {
  __typename: 'UnpartitionedAssetConditionEvaluationNode';
  description: string;
  startTimestamp: number | null;
  endTimestamp: number | null;
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

export type PartitionedAssetConditionEvaluationNodeFragment = {
  __typename: 'PartitionedAssetConditionEvaluationNode';
  description: string;
  startTimestamp: number | null;
  endTimestamp: number | null;
  numTrue: number;
  uniqueId: string;
  childUniqueIds: Array<string>;
  numCandidates: number | null;
};

export type NewEvaluationNodeFragment = {
  __typename: 'AutomationConditionEvaluationNode';
  uniqueId: string;
  expandedLabel: Array<string>;
  userLabel: string | null;
  startTimestamp: number | null;
  endTimestamp: number | null;
  numCandidates: number | null;
  numTrue: number;
  isPartitioned: boolean;
  childUniqueIds: Array<string>;
};

export type AssetConditionEvaluationRecordFragment = {
  __typename: 'AssetConditionEvaluationRecord';
  id: string;
  evaluationId: any;
  numRequested: number;
  runIds: Array<string>;
  timestamp: number;
  startTimestamp: number | null;
  endTimestamp: number | null;
  isLegacy: boolean;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  evaluation: {
    __typename: 'AssetConditionEvaluation';
    rootUniqueId: string;
    evaluationNodes: Array<
      | {
          __typename: 'PartitionedAssetConditionEvaluationNode';
          description: string;
          startTimestamp: number | null;
          endTimestamp: number | null;
          numTrue: number;
          uniqueId: string;
          childUniqueIds: Array<string>;
          numCandidates: number | null;
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
          __typename: 'UnpartitionedAssetConditionEvaluationNode';
          description: string;
          startTimestamp: number | null;
          endTimestamp: number | null;
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
    numTrue: number;
    isPartitioned: boolean;
    childUniqueIds: Array<string>;
  }>;
};

export type GetEvaluationsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  limit: Types.Scalars['Int']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type GetEvaluationsQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        currentAutoMaterializeEvaluationId: any | null;
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
          evaluationId: any;
          numRequested: number;
          runIds: Array<string>;
          timestamp: number;
          startTimestamp: number | null;
          endTimestamp: number | null;
          isLegacy: boolean;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
          evaluation: {
            __typename: 'AssetConditionEvaluation';
            rootUniqueId: string;
            evaluationNodes: Array<
              | {
                  __typename: 'PartitionedAssetConditionEvaluationNode';
                  description: string;
                  startTimestamp: number | null;
                  endTimestamp: number | null;
                  numTrue: number;
                  uniqueId: string;
                  childUniqueIds: Array<string>;
                  numCandidates: number | null;
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
              | {
                  __typename: 'UnpartitionedAssetConditionEvaluationNode';
                  description: string;
                  startTimestamp: number | null;
                  endTimestamp: number | null;
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
            numTrue: number;
            isPartitioned: boolean;
            childUniqueIds: Array<string>;
          }>;
        }>;
      }
    | {__typename: 'AutoMaterializeAssetEvaluationNeedsMigrationError'; message: string}
    | null;
};

export type GetEvaluationsSpecificPartitionQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  evaluationId: Types.Scalars['BigInt']['input'];
  partition: Types.Scalars['String']['input'];
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
          numTrue: number;
          uniqueId: string;
          childUniqueIds: Array<string>;
          numCandidates: number | null;
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
          __typename: 'UnpartitionedAssetConditionEvaluationNode';
          description: string;
          startTimestamp: number | null;
          endTimestamp: number | null;
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

export const GetEvaluationsQueryVersion = '72294147655740415d3bdaf8de190465417ec4352927fbdcda7c65eadd75dd50';

export const GetEvaluationsSpecificPartitionQueryVersion = 'd753be21aeea04a8cb0fa20e6933463ca16c19413df0741bd94b5a06dd8d1de7';
