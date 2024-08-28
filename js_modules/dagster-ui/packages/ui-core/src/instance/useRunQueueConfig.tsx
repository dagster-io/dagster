import {
  InstanceRunQueueConfigQuery,
  InstanceRunQueueConfigQueryVariables,
} from './types/useRunQueueConfig.types';
import {gql, useQuery} from '../apollo-client';

export const useRunQueueConfig = () => {
  const queryResult = useQuery<InstanceRunQueueConfigQuery, InstanceRunQueueConfigQueryVariables>(
    INSTANCE_RUN_QUEUE_CONFIG,
  );
  return queryResult.data?.instance.runQueueConfig;
};

const INSTANCE_RUN_QUEUE_CONFIG = gql`
  query InstanceRunQueueConfig {
    instance {
      id
      hasInfo
      runQueueConfig {
        maxConcurrentRuns
        tagConcurrencyLimitsYaml
        isOpConcurrencyAware
      }
    }
  }
`;
