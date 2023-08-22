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
          rulesWithRuleEvaluations: Array<{
            __typename: 'AutoMaterializeRuleWithRuleEvaluations';
            rule: {__typename: 'AutoMaterializeRule'; description: string} | null;
            ruleEvaluations: Array<{
              __typename: 'AutoMaterializeRuleEvaluation';
              partitionKeysOrError:
                | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
                | {__typename: 'PartitionSubsetDeserializationError'; message: string}
                | null;
            }>;
          }>;
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
  rulesWithRuleEvaluations: Array<{
    __typename: 'AutoMaterializeRuleWithRuleEvaluations';
    rule: {__typename: 'AutoMaterializeRule'; description: string} | null;
    ruleEvaluations: Array<{
      __typename: 'AutoMaterializeRuleEvaluation';
      partitionKeysOrError:
        | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
        | {__typename: 'PartitionSubsetDeserializationError'; message: string}
        | null;
    }>;
  }>;
};

export type AutoMateralizeWithConditionFragment = {
  __typename: 'AutoMaterializeRuleWithRuleEvaluations';
  rule: {__typename: 'AutoMaterializeRule'; description: string} | null;
  ruleEvaluations: Array<{
    __typename: 'AutoMaterializeRuleEvaluation';
    partitionKeysOrError:
      | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
      | {__typename: 'PartitionSubsetDeserializationError'; message: string}
      | null;
  }>;
};
