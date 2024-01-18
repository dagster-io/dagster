// Generated GraphQL types, do not edit manually.
import * as Types from '../../graphql/types';

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
