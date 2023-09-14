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
            rule: {
              __typename: 'AutoMaterializeRule';
              description: string;
              decisionType: Types.AutoMaterializeDecisionType;
              className: string;
            };
            ruleEvaluations: Array<{
              __typename: 'AutoMaterializeRuleEvaluation';
              evaluationData:
                | {
                    __typename: 'ParentMaterializedRuleEvaluationData';
                    updatedAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
                    willUpdateAssetKeys: Array<{
                      __typename: 'AssetKey';
                      path: Array<string>;
                    }> | null;
                  }
                | {__typename: 'TextRuleEvaluationData'; text: string | null}
                | {
                    __typename: 'WaitingOnKeysRuleEvaluationData';
                    waitingOnAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
                  }
                | null;
              partitionKeysOrError:
                | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
                | {__typename: 'PartitionSubsetDeserializationError'; message: string}
                | null;
            }>;
          }>;
          rules: Array<{
            __typename: 'AutoMaterializeRule';
            description: string;
            decisionType: Types.AutoMaterializeDecisionType;
            className: string;
          }> | null;
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
    rule: {
      __typename: 'AutoMaterializeRule';
      description: string;
      decisionType: Types.AutoMaterializeDecisionType;
      className: string;
    };
    ruleEvaluations: Array<{
      __typename: 'AutoMaterializeRuleEvaluation';
      evaluationData:
        | {
            __typename: 'ParentMaterializedRuleEvaluationData';
            updatedAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
            willUpdateAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
          }
        | {__typename: 'TextRuleEvaluationData'; text: string | null}
        | {
            __typename: 'WaitingOnKeysRuleEvaluationData';
            waitingOnAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
          }
        | null;
      partitionKeysOrError:
        | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
        | {__typename: 'PartitionSubsetDeserializationError'; message: string}
        | null;
    }>;
  }>;
  rules: Array<{
    __typename: 'AutoMaterializeRule';
    description: string;
    decisionType: Types.AutoMaterializeDecisionType;
    className: string;
  }> | null;
};

export type RuleWithEvaluationsFragment = {
  __typename: 'AutoMaterializeRuleWithRuleEvaluations';
  rule: {
    __typename: 'AutoMaterializeRule';
    description: string;
    decisionType: Types.AutoMaterializeDecisionType;
    className: string;
  };
  ruleEvaluations: Array<{
    __typename: 'AutoMaterializeRuleEvaluation';
    evaluationData:
      | {
          __typename: 'ParentMaterializedRuleEvaluationData';
          updatedAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
          willUpdateAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
        }
      | {__typename: 'TextRuleEvaluationData'; text: string | null}
      | {
          __typename: 'WaitingOnKeysRuleEvaluationData';
          waitingOnAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
        }
      | null;
    partitionKeysOrError:
      | {__typename: 'PartitionKeys'; partitionKeys: Array<string>}
      | {__typename: 'PartitionSubsetDeserializationError'; message: string}
      | null;
  }>;
};
