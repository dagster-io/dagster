import {Button, Icon, Menu, MenuItem, Popover} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import {useContext, useMemo, useState} from 'react';

import {TimeContext} from '../../app/time/TimeContext';
import {TimeRangeState, calculateTimeRanges} from '../../ui/BaseFilters/useTimeRangeFilter';
import {DateRangeDialog} from '../../ui/DateRangeDialog';
import {useFormatDateTime} from '../../ui/useFormatDateTime';
import {RunFilterToken} from '../RunsFilterUtils';

type RunsDateRangeSelectProps = {
  /** The `created_date_after` and `created_date_before` tokens. */
  tokens: RunFilterToken[];
  onChange: (tokens: RunFilterToken[]) => void;
};

const DATE_FORMAT = {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
} as const satisfies Intl.DateTimeFormatOptions;

// Like `runsFilterForSearchTokens`, the last token of each type wins. Values a `Date` can't hold
// read as no bound, so a malformed link can't break the label.
const getLastBoundMs = (tokens: RunFilterToken[], type: RunFilterToken['token']) => {
  const ms = parseInt(tokens.filter(({token}) => token === type).at(-1)?.value ?? '') * 1000;
  return Number.isNaN(new Date(ms).getTime()) ? null : ms;
};

const getTokensForRange = ([after, before]: TimeRangeState): RunFilterToken[] => [
  ...(after !== null ? [{token: 'created_date_after' as const, value: `${after / 1000}`}] : []),
  ...(before !== null ? [{token: 'created_date_before' as const, value: `${before / 1000}`}] : []),
];

const getRangeLabel = (
  [after, before]: TimeRangeState,
  formatDateTime: ReturnType<typeof useFormatDateTime>,
) => {
  const formatDate = (ms: number) => formatDateTime(new Date(ms), DATE_FORMAT);

  if (after !== null && before !== null) {
    // Compare formatted dates, so a day with a DST shift still reads as one day.
    const afterDate = formatDate(after);
    const beforeDate = formatDate(before);
    return afterDate === beforeDate ? afterDate : `${afterDate} - ${beforeDate}`;
  }
  if (after !== null) {
    return `After ${formatDate(after)}`;
  }
  if (before !== null) {
    return `Before ${formatDate(before)}`;
  }
  return 'All time';
};

export const RunsDateRangeSelect = ({tokens, onChange}: RunsDateRangeSelectProps) => {
  const {resolvedTimezone} = useContext(TimeContext);
  const formatDateTime = useFormatDateTime();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isPickingDateRange, setIsPickingDateRange] = useState(false);

  const {timeRangesArray} = useMemo(
    () => calculateTimeRanges(resolvedTimezone),
    [
      resolvedTimezone,
      // Recalculate once an hour
      // eslint-disable-next-line react-hooks/exhaustive-deps
      Math.floor(Date.now() / (1000 * 60 * 60)),
    ],
  );
  const presets = timeRangesArray.filter(({key}) => key !== 'CUSTOM');

  const range = [
    getLastBoundMs(tokens, 'created_date_after'),
    getLastBoundMs(tokens, 'created_date_before'),
  ] satisfies TimeRangeState;

  const isAllTime = range[0] === null && range[1] === null;
  const preset = presets.find((candidate) => isEqual(candidate.range, range));
  const label = preset ? preset.label : getRangeLabel(range, formatDateTime);

  return (
    <>
      <DateRangeDialog
        isOpen={isPickingDateRange}
        onCancel={() => setIsPickingDateRange(false)}
        onApply={(customRange) => {
          setIsPickingDateRange(false);
          onChange(getTokensForRange(customRange));
        }}
      />
      <Popover
        placement="bottom-start"
        isOpen={isMenuOpen}
        onInteraction={setIsMenuOpen}
        content={
          <Menu>
            {presets.map(({key, label: presetLabel, range: presetRange}) => (
              <MenuItem
                key={key}
                text={presetLabel}
                active={key === preset?.key}
                onClick={() => {
                  setIsMenuOpen(false);
                  onChange(getTokensForRange(presetRange));
                }}
              />
            ))}
            <MenuItem
              text="All time"
              active={isAllTime}
              onClick={() => {
                setIsMenuOpen(false);
                onChange([]);
              }}
            />
            <MenuItem
              text="Custom…"
              onClick={() => {
                setIsMenuOpen(false);
                setIsPickingDateRange(true);
              }}
            />
          </Menu>
        }
      >
        <Button
          aria-label={`Created date: ${label}`}
          icon={<Icon name="calendar" />}
          rightIcon={<Icon name="arrow_drop_down" />}
        >
          {label}
        </Button>
      </Popover>
    </>
  );
};
