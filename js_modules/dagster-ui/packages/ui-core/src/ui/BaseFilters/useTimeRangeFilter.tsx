import {
  Box,
  Button,
  Colors,
  DateRange,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  IconName,
} from '@dagster-io/ui-components';
import {TZDate} from '@date-fns/tz';
import {endOfDay} from 'date-fns';
import dayjs from 'dayjs';
import isEqual from 'lodash/isEqual';
import memoize from 'lodash/memoize';
import {useContext, useMemo, useState} from 'react';

import {FilterObject, FilterTag, FilterTagHighlightedText} from './useFilter';
import {TimeContext} from '../../app/time/TimeContext';
import {browserTimezone} from '../../app/time/browserTimezone';
import {useUpdatingRef} from '../../hooks/useUpdatingRef';
import {lazy} from '../../util/lazy';

const DayPickerWrapper = lazy(() => import('./DayPickerWrapperForLazyImport'));

import '../../util/dayjsExtensions';

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
            {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
            before <FilterTagHighlightedText>{L_FORMAT.format(state[1]!)}</FilterTagHighlightedText>
          </>
        );
      }
      if (!state[1]) {
        return (
          <>
            {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
            after <FilterTagHighlightedText>{L_FORMAT.format(state[0]!)}</FilterTagHighlightedText>
          </>
        );
      }
      if (state[1] - state[0] === (24 * 60 * 60 - 1) * 1000) {
        return (
          <>
            {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
            on <FilterTagHighlightedText>{L_FORMAT.format(state[0]!)}</FilterTagHighlightedText>
          </>
        );
      }
      return (
        <>
          {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
          from <FilterTagHighlightedText>{L_FORMAT.format(state[0]!)}</FilterTagHighlightedText>
          {' through '}
          {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
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

const buildFormatter = memoize(
  (timeZone: string) =>
    new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      timeZone,
    }),
);

interface DialogProps {
  filter: TimeRangeFilter;
  close: () => void;
}

export function CustomTimeRangeFilterDialog({filter, close}: DialogProps) {
  const {
    timezone: [_timezone],
  } = useContext(TimeContext);
  const targetTimezone = _timezone === 'Automatic' ? browserTimezone() : _timezone;

  const [selected, setSelected] = useState<DateRange>(() => ({from: undefined, to: undefined}));

  const [isOpen, setIsOpen] = useState(true);
  const formatter = buildFormatter(targetTimezone);

  const leftContent = () => {
    if (selected.from) {
      if (selected.to) {
        return (
          <div>
            <span style={{color: Colors.textLight()}}>Selected:</span>{' '}
            {formatter.format(selected.from)} - {formatter.format(selected.to)}
          </div>
        );
      }
      return (
        <div>
          Selected{' '}
          <span style={{color: Colors.textLight()}}>{formatter.format(selected.from)}</span>
        </div>
      );
    }

    return null;
  };

  return (
    <Dialog isOpen={isOpen} title="Select a date range" onClosed={close} style={{width: 'auto'}}>
      <DialogBody>
        <div style={{height: '344px'}}>
          <DayPickerWrapper
            timeZone={targetTimezone}
            mode="range"
            navLayout="around"
            selected={selected}
            onSelect={setSelected}
            excludeDisabled
            required
            numberOfMonths={2}
          />
        </div>
      </DialogBody>
      <DialogFooter topBorder left={leftContent()}>
        <Button onClick={() => setIsOpen(false)}>Cancel</Button>
        <Button
          intent="primary"
          disabled={!selected.from || !selected.to}
          onClick={() => {
            if (selected.from && selected.to) {
              const endDateEndOfDay = endOfDay(new TZDate(selected.to, targetTimezone));
              filter.setState([selected.from.valueOf(), endDateEndOfDay.valueOf()]);
              setIsOpen(false);
            }
          }}
        >
          Apply
        </Button>
      </DialogFooter>
    </Dialog>
  );
}
