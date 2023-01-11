import {Colors, CaptionMono} from '@dagster-io/ui';
import * as React from 'react';

import {graphql} from '../graphql';
import {InstigationStatus, ScheduleFutureTicksFragmentFragment} from '../graphql/graphql';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

const TIME_FORMAT = {
  showTimezone: true,
  showSeconds: true,
};

interface Props {
  schedules: ScheduleFutureTicksFragmentFragment[];
}

export const NextTick = (props: Props) => {
  const {schedules} = props;

  const nextTick = React.useMemo(() => {
    const timestamps = schedules.map((schedule) => {
      const {executionTimezone, futureTicks, scheduleState} = schedule;
      if (scheduleState.status === InstigationStatus.RUNNING) {
        return {
          executionTimezone,
          earliest: Math.min(...futureTicks.results.map(({timestamp}) => timestamp)),
        };
      }
      return null;
    });

    return timestamps.reduce((earliestOverall, timestamp) => {
      if (
        !earliestOverall ||
        (timestamp?.earliest && timestamp.earliest < earliestOverall?.earliest)
      ) {
        return timestamp;
      }
      return earliestOverall;
    }, null);
  }, [schedules]);

  if (nextTick) {
    return (
      <CaptionMono color={Colors.Gray500}>
        Next tick:{' '}
        <TimestampDisplay
          timestamp={nextTick.earliest}
          timezone={nextTick.executionTimezone}
          timeFormat={TIME_FORMAT}
        />
      </CaptionMono>
    );
  }

  return null;
};

export const SCHEDULE_FUTURE_TICKS_FRAGMENT = graphql(`
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
`);
