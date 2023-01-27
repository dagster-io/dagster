// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SingleResourceQueryVariables = Types.Exact<{
  selector: Types.ResourceSelector;
}>;

export type SingleResourceQuery = {
  __typename: 'DagitQuery';
  topLevelResourceOrError:
    | {__typename: 'PythonError'}
    | {__typename: 'ResourceNotFoundError'}
    | {__typename: 'TopLevelResource'; description: string | null; name: string};
};
