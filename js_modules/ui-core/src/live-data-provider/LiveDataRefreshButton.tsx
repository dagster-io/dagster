import {Box, Button, Colors, Icon, Tooltip} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import {useEffect, useState} from 'react';

import '../util/dayjsExtensions';

export const LiveDataRefreshButton = ({
  isRefreshing,
  onRefresh,
  oldestDataTimestamp,
}: {
  isRefreshing: boolean;
  onRefresh: () => void;
  oldestDataTimestamp: number;
}) => {
  return (
    <Tooltip
      content={
        isRefreshing ? (
          'Refreshing asset data…'
        ) : (
          <Box flex={{direction: 'column', gap: 4}}>
            <TimeFromNowWithSeconds timestamp={oldestDataTimestamp} />
            <div>Click to refresh now</div>
          </Box>
        )
      }
    >
      <Button
        icon={<Icon name="refresh" color={Colors.accentGray()} />}
        onClick={() => {
          if (!isRefreshing) {
            onRefresh();
          }
        }}
      />
    </Tooltip>
  );
};

export const REFRESHING_DATA = `Refreshing data…`;

const TimeFromNowWithSeconds = ({timestamp}: {timestamp: number}) => {
  const [text, setText] = useState(dayjs(timestamp).fromNow(true));
  useEffect(() => {
    const interval = setInterval(() => {
      setText(dayjs(timestamp).fromNow(true));
    }, 1000);
    return () => {
      clearInterval(interval);
    };
  }, [timestamp]);
  return <>{text === '0s' ? REFRESHING_DATA : `Data is at most ${text} old`}</>;
};
