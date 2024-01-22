import {gql} from '@apollo/client';
import {Colors, MetadataTable} from '@dagster-io/ui-components';
import * as React from 'react';

import {TimeElapsed} from './TimeElapsed';
import {RunTimingFragment} from './types/RunTimingDetails.types';
import {RunStatus} from '../graphql/types';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

export const timingStringForStatus = (status?: RunStatus) => {
  switch (status) {
    case RunStatus.QUEUED:
      return 'Queued';
    case RunStatus.CANCELED:
      return 'Canceled';
    case RunStatus.CANCELING:
      return 'Canceling…';
    case RunStatus.FAILURE:
      return 'Failed';
    case RunStatus.NOT_STARTED:
      return 'Waiting to start…';
    case RunStatus.STARTED:
      return 'Started…';
    case RunStatus.STARTING:
      return 'Starting…';
    case RunStatus.SUCCESS:
      return 'Succeeded';
    default:
      return 'None';
  }
};

const LoadingOrValue = ({
  loading,
  children,
}: {
  loading: boolean;
  children: () => React.ReactNode;
}) => (loading ? <div style={{color: Colors.textLight()}}>Loading…</div> : <div>{children()}</div>);

const TIME_FORMAT = {showSeconds: true, showTimezone: false};

export const RunTimingDetails = ({
  loading,
  run,
}: {
  loading: boolean;
  run: RunTimingFragment | undefined;
}) => {
  return (
    <MetadataTable
      spacing={0}
      rows={[
        {
          key: 'Started',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.startTime) {
                  return <TimestampDisplay timestamp={run.startTime} timeFormat={TIME_FORMAT} />;
                }
                return (
                  <div style={{color: Colors.textLight()}}>
                    {timingStringForStatus(run?.status)}
                  </div>
                );
              }}
            </LoadingOrValue>
          ),
        },
        {
          key: 'Ended',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.endTime) {
                  return <TimestampDisplay timestamp={run.endTime} timeFormat={TIME_FORMAT} />;
                }
                return (
                  <div style={{color: Colors.textLight()}}>
                    {timingStringForStatus(run?.status)}
                  </div>
                );
              }}
            </LoadingOrValue>
          ),
        },
        {
          key: 'Duration',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.startTime) {
                  return <TimeElapsed startUnix={run.startTime} endUnix={run.endTime} />;
                }
                return (
                  <div style={{color: Colors.textLight()}}>
                    {timingStringForStatus(run?.status)}
                  </div>
                );
              }}
            </LoadingOrValue>
          ),
        },
      ]}
    />
  );
};

export const RUN_TIMING_FRAGMENT = gql`
  fragment RunTimingFragment on Run {
    id
    startTime
    endTime
    updateTime
    status
    hasConcurrencyKeySlots
  }
`;
