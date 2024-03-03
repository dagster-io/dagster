import {gql, useQuery} from '@apollo/client';

import {
  InstanceRunQueueConcurrencyAwareQuery,
  InstanceRunQueueConcurrencyAwareQueryVariables,
} from './types/useIsRunCoordinatorConcurrencyAware.types';

export const useIsRunCoordinatorConcurrencyAware = () => {
  const {data} = useQuery<
    InstanceRunQueueConcurrencyAwareQuery,
    InstanceRunQueueConcurrencyAwareQueryVariables
  >(INSTANCE_RUN_QUEUE_CONCURRENCY_AWARE);
  return data?.instance.runQueueConfig && data?.instance.runQueueConfig.isOpConcurrencyAware;
};

const INSTANCE_RUN_QUEUE_CONCURRENCY_AWARE = gql`
  query InstanceRunQueueConcurrencyAware {
    instance {
      id
      runQueueConfig {
        isOpConcurrencyAware
      }
    }
  }
`;
