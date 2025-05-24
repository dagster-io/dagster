import {Box, Button, Colors, Dialog, DialogFooter, Icon, IconName} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import isEqual from 'lodash/isEqual';
// eslint-disable-next-line no-restricted-imports
import momentTZ from 'moment-timezone';
import {useContext, useEffect, useMemo, useState} from 'react';
import styles from './useTimeRangeFilter.module.css';

import {FilterObject, FilterTag, FilterTagHighlightedText} from './useFilter';
import {TimeContext} from '../../app/time/TimeContext';
import {browserTimezone} from '../../app/time/browserTimezone';
import {useUpdatingRef} from '../../hooks/useUpdatingRef';
import {lazy} from '../../util/lazy';

const DateRangePicker = lazy(() => import('./DateRangePickerWrapper'));

dayjs.extend(utc);
dayjs.extend(timezone);

export type TimeRangeState = [number | null, number | null];

export function calculateTimeRanges(timezone: string) {
  const targetTimezone = timezone === 'Automatic' ? browserTimezone() : timezone;
  const nowTimestamp = Date.now();
  const startOfDay = dayjs(nowTimestamp).tz(targetTimezone).startOf('day');
  const obj = {
    TODAY: {
      label: 'Today',
      range: [startOfDay.valueOf(), null] as TimeRangeState,
    },
    YESTERDAY: {
      label: 'Yesterday',
      range: [
        dayjs(nowTimestamp).tz(targetTimezone).subtract(1, 'day').startOf('day').valueOf(),
        startOfDay.valueOf(),
      ] as TimeRangeState,
    },
    LAST_7_DAYS: {
      label: 'Within last 7 days',
      range: [
        dayjs(nowTimestamp).tz(targetTimezone).startOf('day').subtract(1, 'week').valueOf(),
        null,
      ] as TimeRangeState,
    },
    LAST_30_DAYS: {
      label: 'Within last 30 days',
      range: [
        dayjs(nowTimestamp).tz(targetTimezone).startOf('day').subtract(30, 'days').valueOf(),
        null,
      ] as TimeRangeState,
    },
    CUSTOM: {label: 'Custom...', range: [null, null] as TimeRangeState},
  };
  const array = Object.keys(obj).map((keyString) => {
    const key = keyString as keyof typeof obj;
    return {
      key,
      label: obj[key].label,
      range: obj[key].range,
    };
  });
  return {timeRanges: obj, timeRangesArray: array};
}

export type TimeRangeFilter = FilterObject & {
  state: TimeRangeState | undefined;
  setState: (state: TimeRangeState) => void;
};

type TimeRangeKey = keyof ReturnType<typeof calculateTimeRanges>['timeRanges'];

type Args = {
  name: string;
  icon: IconName;

  state?: TimeRangeState;
  onStateChanged: (state: TimeRangeState) => void;
  activeFilterTerm?: string;
};

export function useTimeRangeFilter({
  name,
  activeFilterTerm = 'Timestamp',
  icon,
  state,
  onStateChanged,
}: Args): TimeRangeFilter {
  const {
    timezone: [_timezone],
  } = useContext(TimeContext);
  const timezone = _timezone === 'Automatic' ? browserTimezone() : _timezone;

  const {timeRanges, timeRangesArray} = useMemo(
    () => calculateTimeRanges(timezone),
    [
      timezone,
      // Recalculate once an hour
      // eslint-disable-next-line react-hooks/exhaustive-deps
      Math.floor(Date.now() / (1000 * 60 * 60)),
    ],
  );

  const onReset = () => {
    onStateChanged?.([null, null]);
  };

  const filterObj = useMemo(
    () => ({
      name,
      icon,
      state,
      setState: onStateChanged,
      isActive: !!state && (state[0] !== null || state[1] !== null),
      getResults: (
        query: string,
      ): {
        label: JSX.Element;
        key: string;
        value: TimeRangeKey;
      }[] => {
        return timeRangesArray
          .filter(({label}) => query === '' || label.toLowerCase().includes(query.toLowerCase()))
          .map(({label, key}) => ({
            label: <TimeRangeResult range={label} />,
            key,
            value: key,
          }));
      },
      onSelect: ({
        value,
        close,
        createPortal,
      }: {
        value: TimeRangeKey;
        close: () => void;
        createPortal: (element: JSX.Element) => () => void;
      }) => {
        if (value === 'CUSTOM') {
          const closeFn = createPortal(
            <CustomTimeRangeFilterDialog
              filter={filterObjRef.current}
              close={() => {
                closeFn();
              }}
            />,
          );
        } else {
          const nextState = timeRanges[value].range;
          onStateChanged?.(nextState);
        }
        close();
      },
      activeJSX: (
        <ActiveFilterState
          activeFilterTerm={activeFilterTerm}
          timeRanges={timeRanges}
          state={state}
          timezone={timezone}
          remove={onReset}
        />
      ),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [name, icon, state, timeRanges, timezone, timeRangesArray, activeFilterTerm],
  );
  const filterObjRef = useUpdatingRef(filterObj);
  return filterObj;
}

function TimeRangeResult({range}: {range: string}) {
  return (
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
      <Icon name="date" color={Colors.accentPrimary()} />
      {range}
    </Box>
  );
}

export function ActiveFilterState({
  activeFilterTerm,
  state,
  remove,
  timezone,
  timeRanges,
}: {
  activeFilterTerm: string;
  state: TimeRangeState | undefined;
  remove: () => void;
  timezone: string;
  timeRanges: ReturnType<typeof calculateTimeRanges>['timeRanges'];
}) {
  const L_FORMAT = useMemo(
    () =>
      new Intl.DateTimeFormat(navigator.language, {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        timeZone: timezone,
      }),
    [timezone],
  );
  const dateLabel = useMemo(() => {
    if (!state) {
      return null;
    }

    if (isEqual(state, timeRanges.TODAY.range)) {
      return (
        <>
          <FilterTagHighlightedText>Today</FilterTagHighlightedText>
        </>
      );
    } else if (isEqual(state, timeRanges.YESTERDAY.range)) {
      return (
        <>
          <FilterTagHighlightedText>Yesterday</FilterTagHighlightedText>
        </>
      );
    } else if (isEqual(state, timeRanges.LAST_7_DAYS.range)) {
      return (
        <>
          in <FilterTagHighlightedText>Last 7 days</FilterTagHighlightedText>
        </>
      );
    } else if (isEqual(state, timeRanges.LAST_30_DAYS.range)) {
      return (
        <>
          in <FilterTagHighlightedText>Last 30 days</FilterTagHighlightedText>
        </>
      );
    } else {
      if (!state[0]) {
        return (
          <>
            before <FilterTagHighlightedText>{L_FORMAT.format(state[1]!)}</FilterTagHighlightedText>
          </>
        );
      }
      if (!state[1]) {
        return (
          <>
            after <FilterTagHighlightedText>{L_FORMAT.format(state[0]!)}</FilterTagHighlightedText>
          </>
        );
      }
      if (state[1] - state[0] === (24 * 60 * 60 - 1) * 1000) {
        return (
          <>
            on
            <FilterTagHighlightedText>{L_FORMAT.format(state[0]!)}</FilterTagHighlightedText>
          </>
        );
      }
      return (
        <>
          from <FilterTagHighlightedText>{L_FORMAT.format(state[0]!)}</FilterTagHighlightedText>
          {' through '}
          <FilterTagHighlightedText>{L_FORMAT.format(state[1]!)}</FilterTagHighlightedText>
        </>
      );
    }
  }, [L_FORMAT, state, timeRanges]);

  if (!state) {
    return null;
  }

  return (
    <FilterTag
      iconName="date"
      label={
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          {activeFilterTerm} {dateLabel}
        </Box>
      }
      onRemove={remove}
    />
  );
}

export function CustomTimeRangeFilterDialog({
  filter,
  close,
}: {
  filter: TimeRangeFilter;
  close: () => void;
}) {
  const {
    timezone: [_timezone],
  } = useContext(TimeContext);
  const targetTimezone = _timezone === 'Automatic' ? browserTimezone() : _timezone;

  useEffect(() => {
    const originalDefaultTimezone = momentTZ.tz.guess();
    momentTZ.tz.setDefault(targetTimezone);
    return () => {
      momentTZ.tz.setDefault(originalDefaultTimezone);
    };
  }, [targetTimezone]);

  const [startDate, setStartDate] = useState<moment.Moment | null>(null);
  const [endDate, setEndDate] = useState<moment.Moment | null>(null);
  const [focusedInput, setFocusedInput] = useState<'startDate' | 'endDate'>('startDate');

  const [isOpen, setIsOpen] = useState(true);

  return (
    <Dialog isOpen={isOpen} title="Select a date range" onClosed={close} style={{width: '652px'}}>
      <div className={styles.container}>
        <Box flex={{direction: 'row', gap: 8}} padding={16}>
          <DateRangePicker
            minimumNights={0}
            onDatesChange={({startDate, endDate}) => {
              setStartDate(startDate ? startDate.clone().startOf('day') : null);
              setEndDate(endDate ? endDate.clone().endOf('day') : null);
            }}
            onFocusChange={(focusedInput) => {
              if (focusedInput) {
                setFocusedInput(focusedInput);
              }
            }}
            startDate={startDate}
            endDate={endDate}
            startDateId="start"
            endDateId="end"
            focusedInput={focusedInput}
            withPortal={false}
            keepOpenOnDateSelect
            isOutsideRange={() => false}
          />
        </Box>
      </div>
      <DialogFooter topBorder>
        <Button
          onClick={() => {
            setIsOpen(false);
          }}
        >
          Cancel
        </Button>
        <Button
          intent="primary"
          disabled={!startDate || !endDate}
          onClick={() => {
            filter.setState([startDate!.valueOf(), endDate!.valueOf()]);
            setIsOpen(false);
          }}
        >
          Apply
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

