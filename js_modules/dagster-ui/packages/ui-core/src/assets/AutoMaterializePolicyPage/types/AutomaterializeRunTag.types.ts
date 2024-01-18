// Generated GraphQL types, do not edit manually.
import * as Types from '../../../graphql/types';

export type RunStatusOnlyQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID'];
}>;

export type RunStatusOnlyQuery = {
  __typename: 'Query';
  runOrError:
    | {__typename: 'PythonError'}
    | {__typename: 'Run'; id: string; status: Types.RunStatus}
    | {__typename: 'RunNotFoundError'};
};
