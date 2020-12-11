import {gql} from '@apollo/client';
import * as React from 'react';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {
  StartSchedule,
  StartSchedule_startSchedule_PythonError,
} from 'src/schedules/types/StartSchedule';
import {
  StopSchedule,
  StopSchedule_stopRunningSchedule_PythonError,
} from 'src/schedules/types/StopSchedule';

export const START_SCHEDULE_MUTATION = gql`
  mutation StartSchedule($scheduleSelector: ScheduleSelector!) {
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
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

export const STOP_SCHEDULE_MUTATION = gql`
  mutation StopSchedule($scheduleOriginId: String!) {
    stopRunningSchedule(scheduleOriginId: $scheduleOriginId) {
      __typename
      ... on ScheduleStateResult {
        scheduleState {
          __typename
          id
          status
          runningCount
        }
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

export const displayScheduleMutationErrors = (data: StartSchedule | StopSchedule) => {
  let error:
    | StartSchedule_startSchedule_PythonError
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
