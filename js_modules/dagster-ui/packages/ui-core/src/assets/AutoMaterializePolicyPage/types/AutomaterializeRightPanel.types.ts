// Generated GraphQL types, do not edit manually.
import * as Types from '../../../graphql/types';

export type GetPolicyInfoQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type GetPolicyInfoQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        freshnessPolicy: {
          __typename: 'FreshnessPolicy';
          maximumLagMinutes: number;
          cronSchedule: string | null;
          cronScheduleTimezone: string | null;
        } | null;
        autoMaterializePolicy: {
          __typename: 'AutoMaterializePolicy';
          policyType: Types.AutoMaterializePolicyType;
          maxMaterializationsPerMinute: number | null;
          rules: Array<{
            __typename: 'AutoMaterializeRule';
            description: string;
            decisionType: Types.AutoMaterializeDecisionType;
          }>;
        } | null;
      }
    | {__typename: 'AssetNotFoundError'};
};
