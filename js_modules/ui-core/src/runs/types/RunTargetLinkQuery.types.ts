// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunFeedTargetAssetSelectionQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
}>;

export type RunFeedTargetAssetSelectionQuery = {
  __typename: 'Query';
  runOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
        assetCheckSelection: Array<{
          __typename: 'AssetCheckhandle';
          name: string;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
        }> | null;
      }
    | {__typename: 'RunNotFoundError'};
};

export const RunFeedTargetAssetSelectionQueryVersion = '6db07b91744e7db869a75f1ab3d04dcd6613469259145917fbc941401988ac06';
