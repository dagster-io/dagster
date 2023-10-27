// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SingleGraphQueryVariables = Types.Exact<{
  selector: Types.GraphSelector;
}>;

export type SingleGraphQuery = {
  __typename: 'Query';
  graphOrError:
    | {__typename: 'Graph'; id: string; name: string; description: string | null}
    | {__typename: 'GraphNotFoundError'}
    | {__typename: 'PythonError'};
};
