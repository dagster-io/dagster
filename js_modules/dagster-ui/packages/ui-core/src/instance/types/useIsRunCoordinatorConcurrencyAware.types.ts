// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceRunQueueConcurrencyAwareQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceRunQueueConcurrencyAwareQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    runQueueConfig: {__typename: 'RunQueueConfig'; isOpConcurrencyAware: boolean | null} | null;
  };
};
