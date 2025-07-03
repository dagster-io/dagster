// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type FreshnessEvaluationEnabledQueryVariables = Types.Exact<{[key: string]: never}>;

export type FreshnessEvaluationEnabledQuery = {
  __typename: 'Query';
  instance: {__typename: 'Instance'; id: string; freshnessEvaluationEnabled: boolean};
};

export type FreshnessStatusQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type FreshnessStatusQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        freshnessStatusInfo: {
          __typename: 'FreshnessStatusInfo';
          freshnessStatus: Types.AssetHealthStatus;
          freshnessStatusMetadata: {
            __typename: 'AssetHealthFreshnessMeta';
            lastMaterializedTimestamp: number | null;
          } | null;
        } | null;
      }
    | {__typename: 'AssetNotFoundError'};
};

export const FreshnessEvaluationEnabledQueryVersion = 'db79450d1d49690ab8e4b843490dbb3b83b7349c2334c619e80e597089cc9d57';

export const FreshnessStatusQueryVersion = '3bb87b020443a031d2b0786e007d175d474896b5ad8b7b06f6f9c4de51b21594';
