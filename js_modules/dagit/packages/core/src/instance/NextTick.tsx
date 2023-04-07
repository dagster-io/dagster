import {gql} from '@apollo/client';

export const SCHEDULE_FUTURE_TICKS_FRAGMENT = gql`
  fragment ScheduleFutureTicksFragment on Schedule {
    id
    executionTimezone
    scheduleState {
      id
      status
    }
    futureTicks(cursor: $tickCursor, until: $ticksUntil) {
      results {
        timestamp
      }
    }
  }
`;
