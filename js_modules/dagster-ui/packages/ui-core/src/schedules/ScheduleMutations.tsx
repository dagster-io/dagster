import {gql} from '../apollo-client';
import {
  ResetScheduleMutation,
  StartThisScheduleMutation,
  StopScheduleMutation,
} from './types/ScheduleMutations.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {INSTIGATION_STATE_BASE_FRAGMENT} from '../instigation/InstigationStateBaseFragment';

export const START_SCHEDULE_MUTATION = gql`
  mutation StartThisSchedule($scheduleSelector: ScheduleSelector!) {
    startSchedule(scheduleSelector: $scheduleSelector) {
      ... on ScheduleStateResult {
        scheduleState {
          id
          ...InstigationStateBaseFragment
        }
      }
      ... on UnauthorizedError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${INSTIGATION_STATE_BASE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const STOP_SCHEDULE_MUTATION = gql`
  mutation StopSchedule($id: String!) {
    stopRunningSchedule(id: $id) {
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

export const RESET_SCHEDULE_MUTATION = gql`
  mutation ResetSchedule($scheduleSelector: ScheduleSelector!) {
    resetSchedule(scheduleSelector: $scheduleSelector) {
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
  data: StartThisScheduleMutation | StopScheduleMutation | ResetScheduleMutation,
) => {
  let error;
  if ('startSchedule' in data && data.startSchedule.__typename === 'PythonError') {
    error = data.startSchedule;
  } else if (
    'stopRunningSchedule' in data &&
    data.stopRunningSchedule.__typename === 'PythonError'
  ) {
    error = data.stopRunningSchedule;
  } else if ('resetSchedule' in data && data.resetSchedule.__typename === 'PythonError') {
    error = data.resetSchedule;
  }

  if (error) {
    showCustomAlert({
      title: 'Schedule Response',
      body: <PythonErrorInfo error={error} />,
    });
  }
};
