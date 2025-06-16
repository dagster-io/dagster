import {gql} from '../apollo-client';

export const FRESHNESS_POLICY_FRAGMENT = gql`
  fragment FreshnessPolicyFragment on InternalFreshnessPolicy {
    ... on TimeWindowFreshnessPolicy {
      failWindowSeconds
      warnWindowSeconds
    }
    ... on CronFreshnessPolicy {
      deadlineCron
      lowerBoundDeltaSeconds
      timezone
    }
  }
`;
