import {gql} from '@apollo/client';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';

import {
  StartThisSchedule,
  StartThisSchedule_startSchedule_PythonError,
} from './types/StartThisSchedule';
import {StopSchedule, StopSchedule_stopRunningSchedule_PythonError} from './types/StopSchedule';

export const START_SCHEDULE_MUTATION = gql`
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

  ${PYTHON_ERROR_FRAGMENT}
`;

export const STOP_SCHEDULE_MUTATION = gql`
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

  ${PYTHON_ERROR_FRAGMENT}
`;

export const displayScheduleMutationErrors = (data: StartThisSchedule | StopSchedule) => {
  let error:
    | StartThisSchedule_startSchedule_PythonError
    | StopSchedule_stopRunningSchedule_PythonError
    | null = null;

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
