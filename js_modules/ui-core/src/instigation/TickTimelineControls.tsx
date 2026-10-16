import {Box, ButtonGroup} from '@dagster-io/ui-components';

import {TimelineRangeControls} from '../runs/TimelineRangeControls';
import {HourWindow} from '../runs/useHourWindow';

// Ticks arrive far more often than runs, so the timeline offers a live view of the last few
// minutes alongside the hour windows used elsewhere.
export type TickWindow = 'live' | HourWindow;

export const LIVE_WINDOW_MS = 5 * 60 * 1000;

const ONE_HOUR_MS = 60 * 60 * 1000;

/** How much time a selected window covers. */
export const tickWindowMs = (tickWindow: TickWindow) =>
  tickWindow === 'live' ? LIVE_WINDOW_MS : Number(tickWindow) * ONE_HOUR_MS;

const LIVE_BUTTON = [{id: 'live' as const, label: 'Live'}];

interface Props {
  tickWindow: TickWindow;
  onSelectTickWindow: (tickWindow: TickWindow) => void;
  onPageEarlier: () => void;
  onPageNow: () => void;
  onPageLater: () => void;
}

export const TickTimelineControls = ({
  tickWindow,
  onSelectTickWindow,
  onPageEarlier,
  onPageNow,
  onPageLater,
}: Props) => (
  <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
    <ButtonGroup<'live'>
      activeItems={new Set(tickWindow === 'live' ? ['live' as const] : [])}
      buttons={LIVE_BUTTON}
      onClick={() => onSelectTickWindow('live')}
    />
    <TimelineRangeControls
      hourWindow={tickWindow === 'live' ? null : tickWindow}
      onSelectHourWindow={onSelectTickWindow}
      onPageEarlier={onPageEarlier}
      onPageNow={onPageNow}
      onPageLater={onPageLater}
    />
  </Box>
);
