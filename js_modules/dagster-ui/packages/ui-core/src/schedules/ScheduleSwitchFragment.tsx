import {gql} from '../apollo-client';

export const SCHEDULE_SWITCH_FRAGMENT = gql`
  fragment ScheduleSwitchFragment on Schedule {
    id
    name
    cronSchedule
    executionTimezone
    scheduleState {
      id
      selectorId
      status
      hasStartPermission
      hasStopPermission
    }
  }
`;
