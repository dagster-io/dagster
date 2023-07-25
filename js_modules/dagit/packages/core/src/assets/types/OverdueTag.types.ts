// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type OverduePopoverQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  timestamp: Types.Scalars['String'];
}>;

export type OverduePopoverQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
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
