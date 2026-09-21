import {Box, Button, ButtonGroup} from '@dagster-io/ui-components';

import {HourWindow} from './useHourWindow';

const HOUR_WINDOW_BUTTONS = [
  {id: '1' as const, label: '1hr'},
  {id: '6' as const, label: '6hr'},
  {id: '12' as const, label: '12hr'},
  {id: '24' as const, label: '24hr'},
];

interface Props {
  // Null leaves the group unselected, for views offering a window outside this set.
  hourWindow: HourWindow | null;
  onSelectHourWindow: (hourWindow: HourWindow) => void;
  onPageEarlier: () => void;
  onPageNow: () => void;
  onPageLater: () => void;
  nowLabel?: string;
}

/**
 * Window size + paging controls shared by the views built on `useTimelineRange`.
 */
export const TimelineRangeControls = ({
  hourWindow,
  onSelectHourWindow,
  onPageEarlier,
  onPageNow,
  onPageLater,
  nowLabel = 'Now',
}: Props) => (
  <Box flex={{direction: 'row', gap: 16, alignItems: 'center'}}>
    <ButtonGroup<HourWindow>
      activeItems={new Set(hourWindow ? [hourWindow] : [])}
      buttons={HOUR_WINDOW_BUTTONS}
      onClick={onSelectHourWindow}
    />
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
      <Button onClick={onPageEarlier}>&larr;</Button>
      <Button onClick={onPageNow}>{nowLabel}</Button>
      <Button onClick={onPageLater}>&rarr;</Button>
    </Box>
  </Box>
);
