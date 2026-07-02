/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type FreshnessPolicyFragment_CronFreshnessPolicy = {
  __typename: 'CronFreshnessPolicy';
  deadlineCron: string;
  lowerBoundDeltaSeconds: number;
  timezone: string;
};

export type FreshnessPolicyFragment_TimeWindowFreshnessPolicy = {
  __typename: 'TimeWindowFreshnessPolicy';
  failWindowSeconds: number;
  warnWindowSeconds: number | null;
};

export type FreshnessPolicyFragment =
  | FreshnessPolicyFragment_CronFreshnessPolicy
  | FreshnessPolicyFragment_TimeWindowFreshnessPolicy;
