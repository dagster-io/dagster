import {Box, Popover, Tag} from '@dagster-io/ui-components';
import * as React from 'react';

import {formatElapsedTime} from '../app/Util';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

import {RunTimingDetails} from './RunTimingDetails';
import {RunTimingFragment} from './types/RunTimingDetails.types';

export const RunTimingTags = ({loading, run}: {loading: boolean; run: RunTimingFragment}) => {
  return (
    <>
      {run?.startTime ? (
        <Popover
          interactionKind="hover"
          placement="bottom"
          content={
            <Box padding={16}>
              <RunTimingDetails run={run} loading={loading} />
            </Box>
          }
        >
          <Tag icon="schedule">
            <TimestampDisplay
              timestamp={run.startTime}
              timeFormat={{showSeconds: true, showTimezone: false}}
            />
          </Tag>
        </Popover>
      ) : run.updateTime ? (
        <Tag icon="schedule">
          <TimestampDisplay
            timestamp={run.updateTime}
            timeFormat={{showSeconds: true, showTimezone: false}}
          />
        </Tag>
      ) : undefined}
      {run?.startTime && run?.endTime ? (
        <Popover
          interactionKind="hover"
          placement="bottom"
          content={
            <Box padding={16}>
              <RunTimingDetails run={run} loading={loading} />
            </Box>
          }
        >
          <Tag icon="timer">
            <span style={{fontVariantNumeric: 'tabular-nums'}}>
              {run?.startTime
                ? formatElapsedTime((run?.endTime * 1000 || Date.now()) - run?.startTime * 1000)
                : '–'}
            </span>
          </Tag>
        </Popover>
      ) : null}
    </>
  );
};
