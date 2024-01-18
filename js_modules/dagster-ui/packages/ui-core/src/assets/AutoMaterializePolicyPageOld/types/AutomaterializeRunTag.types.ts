// Generated GraphQL types, do not edit manually.
import * as Types from '../../../graphql/types';

export type OldRunStatusOnlyQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID'];
}>;

export type OldRunStatusOnlyQuery = {
  __typename: 'Query';
  runOrError:
    | {__typename: 'PythonError'}
    | {__typename: 'Run'; id: string; status: Types.RunStatus}
    | {__typename: 'RunNotFoundError'};
};
