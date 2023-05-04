import {gql} from '@apollo/client';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';

import {StartThisScheduleMutation, StopScheduleMutation} from './types/ScheduleMutations.types';

export const START_SCHEDULE_MUTATION = gql`
  mutation StartThisSchedule($scheduleSelector: ScheduleSelector!) {
    startSchedule(scheduleSelector: $scheduleSelector) {
      ... on ScheduleStateResult {
        scheduleState {
          id
          status
          runningCount
        }
      }
      ... on UnauthorizedError {
        message
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
      ... on ScheduleStateResult {
        scheduleState {
          id
          status
          runningCount
        }
      }
      ... on UnauthorizedError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

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
