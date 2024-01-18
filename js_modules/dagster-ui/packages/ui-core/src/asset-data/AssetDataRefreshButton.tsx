import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import updateLocale from 'dayjs/plugin/updateLocale';
import React from 'react';

import {Box, Button, Icon, Tooltip, colorAccentGray} from '@dagster-io/ui-components';

dayjs.extend(relativeTime);
dayjs.extend(updateLocale);

dayjs.updateLocale('en', {
  relativeTime: {
    future: 'in %s',
    past: '%s ago',
    s: '%d seconds',
    m: 'a minute',
    mm: '%d minutes',
    h: 'an hour',
    hh: '%d hours',
    d: 'a day',
    dd: '%d days',
    M: 'a month',
    MM: '%d months',
    y: 'a year',
    yy: '%d years',
  },
});

export const AssetDataRefreshButton = ({
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
        icon={<Icon name="refresh" color={colorAccentGray()} />}
        onClick={() => {
          if (!isRefreshing) {
            onRefresh();
          }
        }}
      />
    </Tooltip>
  );
};

const TimeFromNowWithSeconds = ({timestamp}: {timestamp: number}) => {
  const [text, setText] = React.useState(dayjs(timestamp).fromNow(true));
  React.useEffect(() => {
    const interval = setInterval(() => {
      setText(dayjs(timestamp).fromNow(true));
    }, 1000);
    return () => {
      clearInterval(interval);
    };
  }, [timestamp]);
  return <>{text === '0s' ? 'Refreshing asset data…' : `Data is at most ${text} old`}</>;
};
