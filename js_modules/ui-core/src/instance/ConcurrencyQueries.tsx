import {gql} from '../apollo-client';

export const SET_CONCURRENCY_LIMIT_MUTATION = gql`
  mutation SetConcurrencyLimit($concurrencyKey: String!, $limit: Int!) {
    setConcurrencyLimit(concurrencyKey: $concurrencyKey, limit: $limit)
  }
`;

export const DELETE_CONCURRENCY_LIMIT_MUTATION = gql`
  mutation DeleteConcurrencyLimit($concurrencyKey: String!) {
    deleteConcurrencyLimit(concurrencyKey: $concurrencyKey)
  }
`;

export const FREE_CONCURRENCY_SLOTS_MUTATION = gql`
  mutation FreeConcurrencySlots($runId: String!, $stepKey: String) {
    freeConcurrencySlots(runId: $runId, stepKey: $stepKey)
  }
`;

export const RUNS_FOR_CONCURRENCY_KEY_QUERY = gql`
  query RunsForConcurrencyKeyQuery($filter: RunsFilter, $limit: Int) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      ... on Runs {
        results {
          id
          status
        }
      }
    }
  }
`;
