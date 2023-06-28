// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type GetEvaluationsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  limit: Types.Scalars['Int'];
  cursor?: Types.InputMaybe<Types.Scalars['String']>;
}>;

export type GetEvaluationsQuery = {
  __typename: 'DagitQuery';
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
          conditions: Array<
            | {
                __typename: 'DownstreamFreshnessAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
              }
            | {
                __typename: 'FreshnessAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
              }
            | {
                __typename: 'MaxMaterializationsExceededAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
              }
            | {
                __typename: 'MissingAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
              }
            | {
                __typename: 'ParentMaterializedAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
              }
            | {
                __typename: 'ParentOutdatedAutoMaterializeCondition';
                decisionType: Types.AutoMaterializeDecisionType;
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
  conditions: Array<
    | {
        __typename: 'DownstreamFreshnessAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
      }
    | {
        __typename: 'FreshnessAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
      }
    | {
        __typename: 'MaxMaterializationsExceededAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
      }
    | {
        __typename: 'MissingAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
      }
    | {
        __typename: 'ParentMaterializedAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
      }
    | {
        __typename: 'ParentOutdatedAutoMaterializeCondition';
        decisionType: Types.AutoMaterializeDecisionType;
      }
  >;
};
