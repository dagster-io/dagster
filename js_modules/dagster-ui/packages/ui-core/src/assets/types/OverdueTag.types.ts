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
        internalFreshnessPolicy: {
          __typename: 'TimeWindowFreshnessPolicy';
          failWindowSeconds: number;
          warnWindowSeconds: number | null;
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

export const OverduePopoverQueryVersion = 'ed122f625cc6273c4c997f4d7225e14056aab98d07a08401af2136577a20fbb7';
