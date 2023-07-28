// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SingleNonSdaAssetQueryVariables = Types.Exact<{
  input: Types.AssetKeyInput;
}>;

export type SingleNonSdaAssetQuery = {
  __typename: 'Query';
  assetOrError:
    | {
        __typename: 'Asset';
        id: string;
        assetMaterializations: Array<{
          __typename: 'MaterializationEvent';
          runId: string;
          timestamp: string;
        }>;
      }
    | {__typename: 'AssetNotFoundError'};
};
