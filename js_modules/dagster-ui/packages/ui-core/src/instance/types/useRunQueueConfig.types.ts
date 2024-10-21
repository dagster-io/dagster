// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceRunQueueConfigQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceRunQueueConfigQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    hasInfo: boolean;
    runQueueConfig: {
      __typename: 'RunQueueConfig';
      maxConcurrentRuns: number;
      tagConcurrencyLimitsYaml: string | null;
      isOpConcurrencyAware: boolean | null;
    } | null;
  };
};

export const InstanceRunQueueConfigVersion = '51de03303f49487cecbfbcd9a6624b8999779a88412c035aced402cb295e40c5';
