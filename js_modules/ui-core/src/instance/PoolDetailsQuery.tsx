import {gql} from '../apollo-client';

const CONCURRENCY_STEP_FRAGMENT = gql`
  fragment ConcurrencyStepFragment on PendingConcurrencyStep {
    runId
    stepKey
    enqueuedTimestamp
    assignedTimestamp
    priority
  }
`;
const CONCURRENCY_LIMIT_FRAGMENT = gql`
  fragment ConcurrencyLimitFragment on ConcurrencyKeyInfo {
    concurrencyKey
    limit
    slotCount
    claimedSlots {
      runId
      stepKey
    }
    pendingSteps {
      ...ConcurrencyStepFragment
    }
    usingDefaultLimit
  }
  ${CONCURRENCY_STEP_FRAGMENT}
`;

export const POOL_DETAILS_QUERY = gql`
  query PoolDetailsQuery($pool: String!) {
    instance {
      id
      minConcurrencyLimitValue
      maxConcurrencyLimitValue
      poolConfig {
        poolGranularity
        defaultPoolLimit
        opGranularityRunBuffer
      }
      runQueuingSupported
      concurrencyLimit(concurrencyKey: $pool) {
        ...ConcurrencyLimitFragment
      }
    }
  }
  ${CONCURRENCY_LIMIT_FRAGMENT}
`;
