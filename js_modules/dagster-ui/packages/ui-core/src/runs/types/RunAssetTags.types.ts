// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunAssetsQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
}>;

export type RunAssetsQuery = {
  __typename: 'Query';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        assets: Array<{
          __typename: 'Asset';
          id: string;
          key: {__typename: 'AssetKey'; path: Array<string>};
        }>;
      }
    | {__typename: 'RunNotFoundError'};
};

export const RunAssetsQueryVersion = '53c1e7814d451dfd58fb2427dcb326a1e9628c8bbc91b3b9c76f8d6c7b75e278';
