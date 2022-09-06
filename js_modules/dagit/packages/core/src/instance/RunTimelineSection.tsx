import {Box, Button, ButtonGroup, Colors, Icon, Heading} from '@dagster-io/ui';
import * as React from 'react';

import {QueryfulRunTimeline} from '../runs/QueryfulRunTimeline';
import {HourWindow, useHourWindow} from '../runs/useHourWindow';

const LOOKAHEAD_HOURS = 1;
const ONE_HOUR = 60 * 60 * 1000;

export const RunTimelineSection = ({
  loading,
  visibleJobKeys,
}: {
  loading: boolean;
  visibleJobKeys: Set<string>;
}) => {
  const [shown, setShown] = React.useState(true);
  const [hourWindow, setHourWindow] = useHourWindow('12');
  const nowRef = React.useRef(Date.now());

  React.useEffect(() => {
    if (!loading) {
      nowRef.current = Date.now();
    }
  }, [loading]);

  const nowSecs = Math.floor(nowRef.current / 1000);
  const range: [number, number] = React.useMemo(() => {
    return [
      nowSecs * 1000 - Number(hourWindow) * ONE_HOUR,
      nowSecs * 1000 + LOOKAHEAD_HOURS * ONE_HOUR,
    ];
  }, [hourWindow, nowSecs]);

  const [start, end] = React.useMemo(() => {
    const [unvalidatedStart, unvalidatedEnd] = range;
    return unvalidatedEnd < unvalidatedStart
      ? [unvalidatedEnd, unvalidatedStart]
      : [unvalidatedStart, unvalidatedEnd];
  }, [range]);

  return (
    <>
      <Box
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        margin={{top: 16}}
        padding={{bottom: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <Box flex={{alignItems: 'center', gap: 8}}>
          <Icon name="waterfall_chart" color={Colors.Gray900} size={20} />
          <Heading>Timeline</Heading>
        </Box>
        <Box flex={{alignItems: 'center', gap: 8}}>
          {shown ? (
            <ButtonGroup<HourWindow>
              activeItems={new Set([hourWindow])}
              buttons={[
                {id: '1', label: '1hr'},
                {id: '6', label: '6hr'},
                {id: '12', label: '12hr'},
                {id: '24', label: '24hr'},
              ]}
              onClick={(hrWindow: HourWindow) => setHourWindow(hrWindow)}
            />
          ) : null}
          <Button
            icon={<Icon name={shown ? 'unfold_less' : 'unfold_more'} />}
            onClick={() => setShown((current) => !current)}
          >
            {shown ? 'Hide' : 'Show'}
          </Button>
        </Box>
      </Box>
      {shown ? <QueryfulRunTimeline range={[start, end]} visibleJobKeys={visibleJobKeys} /> : null}
    </>
  );
};
