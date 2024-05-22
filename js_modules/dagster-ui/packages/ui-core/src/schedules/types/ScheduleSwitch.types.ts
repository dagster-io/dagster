// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ScheduleSwitchFragment = {
  __typename: 'Schedule';
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  scheduleState: {
    __typename: 'InstigationState';
    id: string;
    selectorId: string;
    status: Types.InstigationStatus;
  };
};

export type ScheduleStateQueryVariables = Types.Exact<{
  scheduleSelector: Types.ScheduleSelector;
}>;

export type ScheduleStateQuery = {
  __typename: 'Query';
  scheduleOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Schedule';
        id: string;
        scheduleState: {
          __typename: 'InstigationState';
          id: string;
          status: Types.InstigationStatus;
        };
      }
    | {__typename: 'ScheduleNotFoundError'};
};
