import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {graphql} from '../graphql';
import {StartThisScheduleMutation, StopScheduleMutation} from '../graphql/graphql';

export const START_SCHEDULE_MUTATION = graphql(`
  mutation StartThisSchedule($scheduleSelector: ScheduleSelector!) {
    startSchedule(scheduleSelector: $scheduleSelector) {
      __typename
      ... on ScheduleStateResult {
        scheduleState {
          __typename
          id
          status
          runningCount
        }
      }
      ...PythonErrorFragment
    }
  }
`);

export const STOP_SCHEDULE_MUTATION = graphql(`
  mutation StopSchedule($scheduleOriginId: String!, $scheduleSelectorId: String!) {
    stopRunningSchedule(
      scheduleOriginId: $scheduleOriginId
      scheduleSelectorId: $scheduleSelectorId
    ) {
      __typename
      ... on ScheduleStateResult {
        scheduleState {
          __typename
          id
          status
          runningCount
        }
      }
      ...PythonErrorFragment
    }
  }
`);

export const displayScheduleMutationErrors = (
  data: StartThisScheduleMutation | StopScheduleMutation,
) => {
  let error;
  if ('startSchedule' in data && data.startSchedule.__typename === 'PythonError') {
    error = data.startSchedule;
  } else if (
    'stopRunningSchedule' in data &&
    data.stopRunningSchedule.__typename === 'PythonError'
  ) {
    error = data.stopRunningSchedule;
  }

  if (error) {
    showCustomAlert({
      title: 'Schedule Response',
      body: <PythonErrorInfo error={error} />,
    });
  }
};
