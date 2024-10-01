// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type RunStatusOnlyQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
}>;

export type RunStatusOnlyQuery = {
  __typename: 'Query';
  runOrError:
    | {__typename: 'PythonError'}
    | {__typename: 'Run'; id: string; status: Types.RunStatus}
    | {__typename: 'RunNotFoundError'};
};

export const RunStatusOnlyQueryVersion = 'e0000c8f2600dbe29f305febb04cca005e08da6a7ce03ec20476c59d607495c0';
