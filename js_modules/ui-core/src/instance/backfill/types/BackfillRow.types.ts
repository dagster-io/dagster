// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type SingleBackfillQueryVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
}>;

export type SingleBackfillQuery = {
  __typename: 'Query';
  partitionBackfillOrError:
    | {__typename: 'BackfillNotFoundError'}
    | {
        __typename: 'PartitionBackfill';
        id: string;
        cancelableRuns: Array<{
          __typename: 'Run';
          id: string;
          runId: string;
          status: Types.RunStatus;
        }>;
      }
    | {__typename: 'PythonError'};
};

export const SingleBackfillQueryVersion = 'c2b27d4666926a1c0bfd0c7cfabf9840c67e33a0a374651ee8e52bdec395aa56';
