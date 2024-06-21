// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type BackfillLogsPageQueryVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type BackfillLogsPageQuery = {
  __typename: 'Query';
  partitionBackfillOrError:
    | {__typename: 'BackfillNotFoundError'; message: string}
    | {
        __typename: 'PartitionBackfill';
        id: string;
        logEvents: {
          __typename: 'InstigationEventConnection';
          cursor: string;
          hasMore: boolean;
          events: Array<{
            __typename: 'InstigationEvent';
            message: string;
            timestamp: string;
            level: Types.LogLevel;
          }>;
        };
      }
    | {__typename: 'PythonError'; message: string};
};
