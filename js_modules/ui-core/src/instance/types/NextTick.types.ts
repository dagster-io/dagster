/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type ScheduleFutureTicksFragment = {
  __typename: 'Schedule';
  id: string;
  executionTimezone: string | null;
  scheduleState: {__typename: 'InstigationState'; id: string; status: Types.InstigationStatus};
  futureTicks: {
    __typename: 'DryRunInstigationTicks';
    results: Array<{__typename: 'DryRunInstigationTick'; timestamp: number | null}>;
  };
};
