// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type CodeLocationStatusQueryVariables = Types.Exact<{[key: string]: never}>;

export type CodeLocationStatusQuery = {
  __typename: 'Query';
  locationStatusesOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'WorkspaceLocationStatusEntries';
        entries: Array<{
          __typename: 'WorkspaceLocationStatusEntry';
          id: string;
          name: string;
          loadStatus: Types.RepositoryLocationLoadStatus;
        }>;
      };
};
