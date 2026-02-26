import {gql} from '../apollo-client';

export const QUEUED_RUN_CRITERIA_QUERY = gql`
  query QueuedRunCriteriaQuery($runId: ID!) {
    instance {
      id
      poolConfig {
        poolGranularity
      }
    }
    runOrError(runId: $runId) {
      ... on Run {
        id
        rootConcurrencyKeys
        hasUnconstrainedRootNodes
        allPools
      }
    }
  }
`;
