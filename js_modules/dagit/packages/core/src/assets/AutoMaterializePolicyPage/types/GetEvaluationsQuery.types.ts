// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type GetEvaluationsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  limit: Types.Scalars['Int'];
  cursor?: Types.InputMaybe<Types.Scalars['String']>;
}>;

export type GetEvaluationsQuery = {
  __typename: 'Query';
  autoMaterializeAssetEvaluationsOrError:
    | {__typename: 'AutoMaterializeAssetEvaluationNeedsMigrationError'; message: string}
    | {
        __typename: 'AutoMaterializeAssetEvaluationRecords';
        currentEvaluationId: number | null;
        records: Array<{
          __typename: 'AutoMaterializeAssetEvaluationRecord';
          id: string;
          evaluationId: number;
          numRequested: number;
          numSkipped: number;
          numDiscarded: number;
          timestamp: number;
          runIds: Array<string>;
          conditions: Array<
            | {
                __typename: 'DownstreamFreshnessAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
                partitionKeysOrError:
                  | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
                  | {__typename: 'PartitionSubsetDeserializationError'}
                  | null;
              }
            | {
                __typename: 'FreshnessAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
                partitionKeysOrError:
                  | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
                  | {__typename: 'PartitionSubsetDeserializationError'}
                  | null;
              }
            | {
                __typename: 'MaxMaterializationsExceededAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
                partitionKeysOrError:
                  | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
                  | {__typename: 'PartitionSubsetDeserializationError'}
                  | null;
              }
            | {
                __typename: 'MissingAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
                partitionKeysOrError:
                  | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
                  | {__typename: 'PartitionSubsetDeserializationError'}
                  | null;
              }
            | {
                __typename: 'ParentMaterializedAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
                partitionKeysOrError:
                  | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
                  | {__typename: 'PartitionSubsetDeserializationError'}
                  | null;
              }
            | {
                __typename: 'ParentOutdatedAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
                partitionKeysOrError:
                  | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
                  | {__typename: 'PartitionSubsetDeserializationError'}
                  | null;
              }
          >;
        }>;
      }
    | null;
};

export type AutoMaterializeEvaluationRecordItemFragment = {
  __typename: 'AutoMaterializeAssetEvaluationRecord';
  id: string;
  evaluationId: number;
  numRequested: number;
  numSkipped: number;
  numDiscarded: number;
  timestamp: number;
  runIds: Array<string>;
  conditions: Array<
    | {
        __typename: 'DownstreamFreshnessAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
        partitionKeysOrError:
          | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
          | {__typename: 'PartitionSubsetDeserializationError'}
          | null;
      }
    | {
        __typename: 'FreshnessAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
        partitionKeysOrError:
          | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
          | {__typename: 'PartitionSubsetDeserializationError'}
          | null;
      }
    | {
        __typename: 'MaxMaterializationsExceededAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
        partitionKeysOrError:
          | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
          | {__typename: 'PartitionSubsetDeserializationError'}
          | null;
      }
    | {
        __typename: 'MissingAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
        partitionKeysOrError:
          | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
          | {__typename: 'PartitionSubsetDeserializationError'}
          | null;
      }
    | {
        __typename: 'ParentMaterializedAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
        partitionKeysOrError:
          | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
          | {__typename: 'PartitionSubsetDeserializationError'}
          | null;
      }
    | {
        __typename: 'ParentOutdatedAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
        partitionKeysOrError:
          | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
          | {__typename: 'PartitionSubsetDeserializationError'}
          | null;
      }
  >;
};

export type AutoMateralizeWithConditionFragment_DownstreamFreshnessAutoMaterializeCondition_ = {
  __typename: 'DownstreamFreshnessAutoMaterializeCondition';
  decisionType: Types.AutoMaterializeDecisionType;
  partitionKeysOrError:
    | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
    | {__typename: 'PartitionSubsetDeserializationError'}
    | null;
};

export type AutoMateralizeWithConditionFragment_FreshnessAutoMaterializeCondition_ = {
  __typename: 'FreshnessAutoMaterializeCondition';
  decisionType: Types.AutoMaterializeDecisionType;
  partitionKeysOrError:
    | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
    | {__typename: 'PartitionSubsetDeserializationError'}
    | null;
};

export type AutoMateralizeWithConditionFragment_MaxMaterializationsExceededAutoMaterializeCondition_ = {
  __typename: 'MaxMaterializationsExceededAutoMaterializeCondition';
  decisionType: Types.AutoMaterializeDecisionType;
  partitionKeysOrError:
    | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
    | {__typename: 'PartitionSubsetDeserializationError'}
    | null;
};

export type AutoMateralizeWithConditionFragment_MissingAutoMaterializeCondition_ = {
  __typename: 'MissingAutoMaterializeCondition';
  decisionType: Types.AutoMaterializeDecisionType;
  partitionKeysOrError:
    | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
    | {__typename: 'PartitionSubsetDeserializationError'}
    | null;
};

export type AutoMateralizeWithConditionFragment_ParentMaterializedAutoMaterializeCondition_ = {
  __typename: 'ParentMaterializedAutoMaterializeCondition';
  decisionType: Types.AutoMaterializeDecisionType;
  partitionKeysOrError:
    | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
    | {__typename: 'PartitionSubsetDeserializationError'}
    | null;
};

export type AutoMateralizeWithConditionFragment_ParentOutdatedAutoMaterializeCondition_ = {
  __typename: 'ParentOutdatedAutoMaterializeCondition';
  decisionType: Types.AutoMaterializeDecisionType;
  partitionKeysOrError:
    | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
    | {__typename: 'PartitionSubsetDeserializationError'}
    | null;
};

export type AutoMateralizeWithConditionFragment =
  | AutoMateralizeWithConditionFragment_DownstreamFreshnessAutoMaterializeCondition_
  | AutoMateralizeWithConditionFragment_FreshnessAutoMaterializeCondition_
  | AutoMateralizeWithConditionFragment_MaxMaterializationsExceededAutoMaterializeCondition_
  | AutoMateralizeWithConditionFragment_MissingAutoMaterializeCondition_
  | AutoMateralizeWithConditionFragment_ParentMaterializedAutoMaterializeCondition_
  | AutoMateralizeWithConditionFragment_ParentOutdatedAutoMaterializeCondition_;
