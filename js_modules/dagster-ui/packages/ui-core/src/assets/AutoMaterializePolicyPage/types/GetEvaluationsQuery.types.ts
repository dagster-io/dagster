// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type GetEvaluationsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  limit: Types.Scalars['Int'];
  cursor?: Types.InputMaybe<Types.Scalars['String']>;
}>;

export type GetEvaluationsQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        currentAutoMaterializeEvaluationId: number | null;
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
          evaluationId: number;
          numRequested: number;
          runIds: Array<string>;
          timestamp: number;
          startTimestamp: number | null;
          endTimestamp: number | null;
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
                  numFalse: number;
                  numSkipped: number;
                  uniqueId: string;
                  childUniqueIds: Array<string>;
                  trueSubset: {
                    __typename: 'AssetSubset';
                    subsetValue: {
                      __typename: 'AssetSubsetValue';
                      isPartitioned: boolean;
                      partitionKeys: Array<string> | null;
                      partitionKeyRanges: Array<{
                        __typename: 'PartitionKeyRange';
                        start: string;
                        end: string;
                      }> | null;
                    };
                  };
                  falseSubset: {
                    __typename: 'AssetSubset';
                    subsetValue: {
                      __typename: 'AssetSubsetValue';
                      isPartitioned: boolean;
                      partitionKeys: Array<string> | null;
                      partitionKeyRanges: Array<{
                        __typename: 'PartitionKeyRange';
                        start: string;
                        end: string;
                      }> | null;
                    };
                  };
                  candidateSubset: {
                    __typename: 'AssetSubset';
                    subsetValue: {
                      __typename: 'AssetSubsetValue';
                      isPartitioned: boolean;
                      partitionKeys: Array<string> | null;
                      partitionKeyRanges: Array<{
                        __typename: 'PartitionKeyRange';
                        start: string;
                        end: string;
                      }> | null;
                    };
                  } | null;
                }
              | {
                  __typename: 'SpecificPartitionAssetConditionEvaluationNode';
                  description: string;
                  status: Types.AssetConditionEvaluationStatus;
                  uniqueId: string;
                  childUniqueIds: Array<string>;
                }
              | {
                  __typename: 'UnpartitionedAssetConditionEvaluationNode';
                  description: string;
                  startTimestamp: number | null;
                  endTimestamp: number | null;
                  status: Types.AssetConditionEvaluationStatus;
                  uniqueId: string;
                  childUniqueIds: Array<string>;
                }
            >;
          };
        }>;
      }
    | {__typename: 'AutoMaterializeAssetEvaluationNeedsMigrationError'; message: string}
    | null;
};

export type AssetConditionEvaluationRecordFragment = {
  __typename: 'AssetConditionEvaluationRecord';
  id: string;
  evaluationId: number;
  numRequested: number;
  runIds: Array<string>;
  timestamp: number;
  startTimestamp: number | null;
  endTimestamp: number | null;
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
          numFalse: number;
          numSkipped: number;
          uniqueId: string;
          childUniqueIds: Array<string>;
          trueSubset: {
            __typename: 'AssetSubset';
            subsetValue: {
              __typename: 'AssetSubsetValue';
              isPartitioned: boolean;
              partitionKeys: Array<string> | null;
              partitionKeyRanges: Array<{
                __typename: 'PartitionKeyRange';
                start: string;
                end: string;
              }> | null;
            };
          };
          falseSubset: {
            __typename: 'AssetSubset';
            subsetValue: {
              __typename: 'AssetSubsetValue';
              isPartitioned: boolean;
              partitionKeys: Array<string> | null;
              partitionKeyRanges: Array<{
                __typename: 'PartitionKeyRange';
                start: string;
                end: string;
              }> | null;
            };
          };
          candidateSubset: {
            __typename: 'AssetSubset';
            subsetValue: {
              __typename: 'AssetSubsetValue';
              isPartitioned: boolean;
              partitionKeys: Array<string> | null;
              partitionKeyRanges: Array<{
                __typename: 'PartitionKeyRange';
                start: string;
                end: string;
              }> | null;
            };
          } | null;
        }
      | {
          __typename: 'SpecificPartitionAssetConditionEvaluationNode';
          description: string;
          status: Types.AssetConditionEvaluationStatus;
          uniqueId: string;
          childUniqueIds: Array<string>;
        }
      | {
          __typename: 'UnpartitionedAssetConditionEvaluationNode';
          description: string;
          startTimestamp: number | null;
          endTimestamp: number | null;
          status: Types.AssetConditionEvaluationStatus;
          uniqueId: string;
          childUniqueIds: Array<string>;
        }
    >;
  };
};

export type UnpartitionedAssetConditionEvaluationNodeFragment = {
  __typename: 'UnpartitionedAssetConditionEvaluationNode';
  description: string;
  startTimestamp: number | null;
  endTimestamp: number | null;
  status: Types.AssetConditionEvaluationStatus;
  uniqueId: string;
  childUniqueIds: Array<string>;
};

export type PartitionedAssetConditionEvaluationNodeFragment = {
  __typename: 'PartitionedAssetConditionEvaluationNode';
  description: string;
  startTimestamp: number | null;
  endTimestamp: number | null;
  numTrue: number;
  numFalse: number;
  numSkipped: number;
  uniqueId: string;
  childUniqueIds: Array<string>;
  trueSubset: {
    __typename: 'AssetSubset';
    subsetValue: {
      __typename: 'AssetSubsetValue';
      isPartitioned: boolean;
      partitionKeys: Array<string> | null;
      partitionKeyRanges: Array<{
        __typename: 'PartitionKeyRange';
        start: string;
        end: string;
      }> | null;
    };
  };
  falseSubset: {
    __typename: 'AssetSubset';
    subsetValue: {
      __typename: 'AssetSubsetValue';
      isPartitioned: boolean;
      partitionKeys: Array<string> | null;
      partitionKeyRanges: Array<{
        __typename: 'PartitionKeyRange';
        start: string;
        end: string;
      }> | null;
    };
  };
  candidateSubset: {
    __typename: 'AssetSubset';
    subsetValue: {
      __typename: 'AssetSubsetValue';
      isPartitioned: boolean;
      partitionKeys: Array<string> | null;
      partitionKeyRanges: Array<{
        __typename: 'PartitionKeyRange';
        start: string;
        end: string;
      }> | null;
    };
  } | null;
};

export type SpecificPartitionAssetConditionEvaluationNodeFragment = {
  __typename: 'SpecificPartitionAssetConditionEvaluationNode';
  description: string;
  status: Types.AssetConditionEvaluationStatus;
  uniqueId: string;
  childUniqueIds: Array<string>;
};

export type AssetSubsetFragment = {
  __typename: 'AssetSubset';
  subsetValue: {
    __typename: 'AssetSubsetValue';
    isPartitioned: boolean;
    partitionKeys: Array<string> | null;
    partitionKeyRanges: Array<{__typename: 'PartitionKeyRange'; start: string; end: string}> | null;
  };
};

export type GetEvaluationsSpecificPartitionQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  evaluationId: Types.Scalars['Int'];
  partition: Types.Scalars['String'];
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
          numFalse: number;
          numSkipped: number;
          uniqueId: string;
          childUniqueIds: Array<string>;
          trueSubset: {
            __typename: 'AssetSubset';
            subsetValue: {
              __typename: 'AssetSubsetValue';
              isPartitioned: boolean;
              partitionKeys: Array<string> | null;
              partitionKeyRanges: Array<{
                __typename: 'PartitionKeyRange';
                start: string;
                end: string;
              }> | null;
            };
          };
          falseSubset: {
            __typename: 'AssetSubset';
            subsetValue: {
              __typename: 'AssetSubsetValue';
              isPartitioned: boolean;
              partitionKeys: Array<string> | null;
              partitionKeyRanges: Array<{
                __typename: 'PartitionKeyRange';
                start: string;
                end: string;
              }> | null;
            };
          };
          candidateSubset: {
            __typename: 'AssetSubset';
            subsetValue: {
              __typename: 'AssetSubsetValue';
              isPartitioned: boolean;
              partitionKeys: Array<string> | null;
              partitionKeyRanges: Array<{
                __typename: 'PartitionKeyRange';
                start: string;
                end: string;
              }> | null;
            };
          } | null;
        }
      | {
          __typename: 'SpecificPartitionAssetConditionEvaluationNode';
          description: string;
          status: Types.AssetConditionEvaluationStatus;
          uniqueId: string;
          childUniqueIds: Array<string>;
        }
      | {
          __typename: 'UnpartitionedAssetConditionEvaluationNode';
          description: string;
          startTimestamp: number | null;
          endTimestamp: number | null;
          status: Types.AssetConditionEvaluationStatus;
          uniqueId: string;
          childUniqueIds: Array<string>;
        }
    >;
  } | null;
};

export type UnpartitionedAssetConditionEvaluationNodeFragment = {
  __typename: 'UnpartitionedAssetConditionEvaluationNode';
  description: string;
  startTimestamp: number | null;
  endTimestamp: number | null;
  status: Types.AssetConditionEvaluationStatus;
  uniqueId: string;
  childUniqueIds: Array<string>;
};

export type PartitionedAssetConditionEvaluationNodeFragment = {
  __typename: 'PartitionedAssetConditionEvaluationNode';
  description: string;
  startTimestamp: number | null;
  endTimestamp: number | null;
  numTrue: number;
  numFalse: number;
  numSkipped: number;
  uniqueId: string;
  childUniqueIds: Array<string>;
  trueSubset: {
    __typename: 'AssetSubset';
    subsetValue: {
      __typename: 'AssetSubsetValue';
      isPartitioned: boolean;
      partitionKeys: Array<string> | null;
      partitionKeyRanges: Array<{
        __typename: 'PartitionKeyRange';
        start: string;
        end: string;
      }> | null;
    };
  };
  falseSubset: {
    __typename: 'AssetSubset';
    subsetValue: {
      __typename: 'AssetSubsetValue';
      isPartitioned: boolean;
      partitionKeys: Array<string> | null;
      partitionKeyRanges: Array<{
        __typename: 'PartitionKeyRange';
        start: string;
        end: string;
      }> | null;
    };
  };
  candidateSubset: {
    __typename: 'AssetSubset';
    subsetValue: {
      __typename: 'AssetSubsetValue';
      isPartitioned: boolean;
      partitionKeys: Array<string> | null;
      partitionKeyRanges: Array<{
        __typename: 'PartitionKeyRange';
        start: string;
        end: string;
      }> | null;
    };
  } | null;
};

export type SpecificPartitionAssetConditionEvaluationNodeFragment = {
  __typename: 'SpecificPartitionAssetConditionEvaluationNode';
  description: string;
  status: Types.AssetConditionEvaluationStatus;
  uniqueId: string;
  childUniqueIds: Array<string>;
};

export type AssetSubsetFragment = {
  __typename: 'AssetSubset';
  subsetValue: {
    __typename: 'AssetSubsetValue';
    isPartitioned: boolean;
    partitionKeys: Array<string> | null;
    partitionKeyRanges: Array<{__typename: 'PartitionKeyRange'; start: string; end: string}> | null;
  };
};
