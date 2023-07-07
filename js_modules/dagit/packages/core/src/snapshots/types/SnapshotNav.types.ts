// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SnapshotQueryVariables = Types.Exact<{
  snapshotId: Types.Scalars['String'];
}>;

export type SnapshotQuery = {
  __typename: 'Query';
  pipelineSnapshotOrError:
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PipelineSnapshot'; id: string; parentSnapshotId: string | null}
    | {__typename: 'PipelineSnapshotNotFoundError'}
    | {__typename: 'PythonError'};
};
