import {Colors, MetadataTable} from '@dagster-io/ui-components';
import * as React from 'react';

import {TimeElapsed} from './TimeElapsed';
import {gql} from '../apollo-client';
import {RunTimingFragment} from './types/RunTimingDetails.types';
import {RunStatus} from '../graphql/types';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

export const timingStringForStatus = (status?: RunStatus) => {
  switch (status) {
    case RunStatus.QUEUED:
      return '已排队';
    case RunStatus.CANCELED:
      return '已取消';
    case RunStatus.CANCELING:
      return '正在取消…';
    case RunStatus.FAILURE:
      return '失败';
    case RunStatus.NOT_STARTED:
      return '等待开始…';
    case RunStatus.STARTED:
      return '已开始…';
    case RunStatus.STARTING:
      return '正在启动…';
    case RunStatus.SUCCESS:
      return '成功';
    default:
      return '无';
  }
};

const LoadingOrValue = ({
  loading,
  children,
}: {
  loading: boolean;
  children: () => React.ReactNode;
}) => (loading ? <div style={{color: Colors.textLight()}}>加载中…</div> : <div>{children()}</div>);

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
          key: '开始时间',
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
          key: '结束时间',
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
          key: '持续时间',
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
