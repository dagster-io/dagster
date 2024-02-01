// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunAssetsQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID'];
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
