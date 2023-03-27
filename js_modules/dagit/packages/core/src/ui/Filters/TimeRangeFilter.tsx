import {IconName, Box, Icon, Colors} from '@dagster-io/ui';
import dayjs from 'dayjs';
import React from 'react';

import {Filter, FilterTag, FilterTagHighlightedText} from './Filter';

function calculateTimeRanges() {
  return {
    TODAY: {
      label: 'Today',
      range: [dayjs().startOf('day').toDate().getTime(), null] as TimeRangeState,
    },
    YESTERDAY: {
      label: 'Yesterday',
      range: [
        dayjs().subtract(1, 'day').startOf('day').toDate().getTime(),
        dayjs().subtract(1, 'day').endOf('day').toDate().getTime(),
      ] as TimeRangeState,
    },
    LAST_7_DAYS: {
      label: 'Within last 7 days',
      range: [dayjs().subtract(7, 'days').toDate().getTime(), null] as TimeRangeState,
    },
    LAST_30_DAYS: {
      label: 'Within last 30 days',
      range: [dayjs().subtract(30, 'days').toDate().getTime(), null] as TimeRangeState,
    },
    CUSTOM: {label: 'Custom...', range: [null, null] as TimeRangeState},
  };
}
type TimeRangeKey = keyof ReturnType<typeof calculateTimeRanges>;
type TimeRangeState = [number | null, number | null];
let TimeRanges: Record<
  TimeRangeKey,
  {label: string; range: TimeRangeState}
> = calculateTimeRanges();

const timeRangesArray = Object.keys(TimeRanges).map((key) => ({
  key: key as TimeRangeKey,
  label: TimeRanges[key].label,
  range: TimeRanges[key].range,
}));

export class TimeRangeFilter extends Filter<TimeRangeState, TimeRangeKey> {
  constructor(name: string, icon: IconName, initialState?: TimeRangeState) {
    super(name, icon, initialState || [null, null]);
  }

  renderActiveFilterState(): JSX.Element | null {
    return (
      <ActiveFilterState
        state={this.getState()}
        remove={() => {
          this.setState([null, null]);
        }}
      />
    );
  }

  isActive(): boolean {
    const [start, end] = this.getState();
    return start !== null || end !== null;
  }

  getResults(query: string): {label: JSX.Element; value: TimeRangeKey}[] {
    if (query === '') {
      return timeRangesArray.map(({label, key}) => ({
        label: <TimeRangeResult range={label} />,
        value: key,
      }));
    }
    return timeRangesArray
      .filter(({label}) => label.toLowerCase().includes(query.toLowerCase()))
      .map(({label, key}) => ({
        label: <TimeRangeResult range={label} />,
        value: key,
      }));
  }

  onSelect(key: TimeRangeKey, setIsDropdownOpen: (isOpen: boolean) => void): JSX.Element | null {
    if (key === 'CUSTOM') {
      // TODO add date range selector component
      return <div />;
    } else {
      TimeRanges = calculateTimeRanges();
      const value = TimeRanges[key].range;
      this.setState(value);
    }
    setIsDropdownOpen(false);
    return null;
  }
}

function TimeRangeResult({range}: {range: string}) {
  return (
    <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
      <Icon name="date" color={Colors.Dark} />
      {range}
    </Box>
  );
}

const L_FORMAT = new Intl.DateTimeFormat(navigator.language, {
  year: 'numeric',
  month: 'numeric',
  day: 'numeric',
  timeZone: 'UTC',
});

function ActiveFilterState({state, remove}: {state: TimeRangeState; remove: () => void}) {
  if (!state[0] && !state[1]) {
    return null;
  }
  const dateLabel = React.useMemo(() => {
    if (areEqual(state, TimeRanges.TODAY.range)) {
      return (
        <>
          is <FilterTagHighlightedText>Today</FilterTagHighlightedText>
        </>
      );
    } else if (areEqual(state, TimeRanges.YESTERDAY.range)) {
      return (
        <>
          is <FilterTagHighlightedText>Yesterday</FilterTagHighlightedText>
        </>
      );
    } else if (areEqual(state, TimeRanges.LAST_7_DAYS.range)) {
      return (
        <>
          is within <FilterTagHighlightedText>Last 7 days</FilterTagHighlightedText>
        </>
      );
    } else if (areEqual(state, TimeRanges.LAST_30_DAYS.range)) {
      return (
        <>
          is within <FilterTagHighlightedText>Last 30 days</FilterTagHighlightedText>
        </>
      );
    } else {
      if (!state[0]) {
        return (
          <>
            is before{' '}
            <FilterTagHighlightedText>{L_FORMAT.format(state[1]!)}</FilterTagHighlightedText>
          </>
        );
      }
      if (!state[1]) {
        return (
          <>
            is after{' '}
            <FilterTagHighlightedText>{L_FORMAT.format(state[0]!)}</FilterTagHighlightedText>
          </>
        );
      }
      return (
        <>
          is in range{' '}
          <FilterTagHighlightedText>{L_FORMAT.format(state[0]!)}</FilterTagHighlightedText>
          {' - '}
          <FilterTagHighlightedText>{L_FORMAT.format(state[1]!)}</FilterTagHighlightedText>
        </>
      );
    }
  }, [TimeRanges, state]);

  return <FilterTag iconName="date" label={<span>Timestamp {dateLabel}</span>} onRemove={remove} />;
}
function areEqual(state1: TimeRangeState, state2: TimeRangeState) {
  return state1[0] === state2[0] && state1[1] === state2[1];
}
