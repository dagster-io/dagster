import {gql} from '../apollo-client';
import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';

export const SCHEDULE_FRAGMENT = gql`
  fragment ScheduleFragment on Schedule {
    id
    name
    cronSchedule
    executionTimezone
    pipelineName
    solidSelection
    mode
    description
    partitionSet {
      id
      name
    }
    defaultStatus
    canReset
    scheduleState {
      id
      ...InstigationStateFragment
    }
    futureTicks(limit: 5) {
      results {
        timestamp
      }
    }
    owners {
      ... on UserDefinitionOwner {
        email
      }
      ... on TeamDefinitionOwner {
        team
      }
    }
  }

  ${INSTIGATION_STATE_FRAGMENT}
`;
