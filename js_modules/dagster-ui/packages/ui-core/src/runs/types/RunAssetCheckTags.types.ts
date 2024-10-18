// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunAssetChecksQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
}>;

export type RunAssetChecksQuery = {
  __typename: 'Query';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        assetChecks: Array<{
          __typename: 'AssetCheckhandle';
          name: string;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
        }> | null;
      }
    | {__typename: 'RunNotFoundError'};
};

export const RunAssetChecksQueryVersion = '6946372fc625c6aba249a54be1943c0858c8efbd5e6f5c64c55723494dc199e4';
