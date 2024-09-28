// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type OverduePopoverQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  timestamp: Types.Scalars['String']['input'];
}>;

export type OverduePopoverQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        freshnessInfo: {
          __typename: 'AssetFreshnessInfo';
          currentLagMinutes: number | null;
          currentMinutesLate: number | null;
        } | null;
        freshnessPolicy: {
          __typename: 'FreshnessPolicy';
          cronSchedule: string | null;
          cronScheduleTimezone: string | null;
          lastEvaluationTimestamp: string | null;
          maximumLagMinutes: number;
        } | null;
        assetMaterializationUsedData: Array<{
          __typename: 'MaterializationUpstreamDataVersion';
          timestamp: string;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
          downstreamAssetKey: {__typename: 'AssetKey'; path: Array<string>};
        }>;
      }
    | {__typename: 'AssetNotFoundError'};
};

export const OverduePopoverQueryVersion = '3c8359e1adfab8237e4b26508489f07c09b24069373064c6c94d645312ae9296';
