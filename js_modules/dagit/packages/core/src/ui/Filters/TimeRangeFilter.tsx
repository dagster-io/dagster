import {IconName, Box, Icon, Colors, Dialog, Button, DialogFooter, TextInput} from '@dagster-io/ui';
import dayjs from 'dayjs';
import isEqual from 'lodash/isEqual';
import React from 'react';
import Calendar from 'react-calendar';
import styled from 'styled-components/macro';

import {Filter, FilterTag, FilterTagHighlightedText} from './Filter';

import 'react-calendar/dist/Calendar.css';

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

  onSelect(
    key: TimeRangeKey,
    setIsDropdownOpen: (isOpen: boolean) => void,
    createPortal: (element: JSX.Element) => () => void,
  ) {
    if (key === 'CUSTOM') {
      const closeRef = {
        current: () => {
          debugger;
        },
      };
      closeRef.current = createPortal(
        <CustomTimeRangeFilterDialog filter={this} closeRef={closeRef} />,
      );
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
  const dateLabel = React.useMemo(() => {
    if (isEqual(state, TimeRanges.TODAY.range)) {
      return (
        <>
          is <FilterTagHighlightedText>Today</FilterTagHighlightedText>
        </>
      );
    } else if (isEqual(state, TimeRanges.YESTERDAY.range)) {
      return (
        <>
          is <FilterTagHighlightedText>Yesterday</FilterTagHighlightedText>
        </>
      );
    } else if (isEqual(state, TimeRanges.LAST_7_DAYS.range)) {
      return (
        <>
          is within <FilterTagHighlightedText>Last 7 days</FilterTagHighlightedText>
        </>
      );
    } else if (isEqual(state, TimeRanges.LAST_30_DAYS.range)) {
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
  }, [state]);

  return <FilterTag iconName="date" label={<span>Timestamp {dateLabel}</span>} onRemove={remove} />;
}

function CustomTimeRangeFilterDialog({
  filter,
  closeRef,
}: {
  filter: TimeRangeFilter;
  closeRef: {current: () => void};
}) {
  const [startDate, setStartDate] = React.useState<string | undefined>(undefined);
  const [endDate, setEndDate] = React.useState<string | undefined>(undefined);

  const [isOpen, setIsOpen] = React.useState(true);

  return (
    <Dialog
      isOpen={isOpen}
      title="Select a date range"
      onClosed={() => {
        // close the portal after the animation is done
        closeRef.current();
      }}
      style={{minWidth: '600px'}}
    >
      <Container>
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}} padding={16}>
          <TextInput
            placeholder="Start date"
            type="date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              if (endDate && new Date(endDate) < new Date(e.target.value)) {
                setEndDate(e.target.value);
              }
            }}
          />
          {' - '}
          <TextInput
            placeholder="End date"
            type="date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              if (startDate && new Date(startDate) > new Date(e.target.value)) {
                setStartDate(e.target.value);
              }
            }}
          />
        </Box>
        <Box flex={{direction: 'row', gap: 8}} padding={16}>
          <Calendar
            value={startDate ? createDateLocalTimezone(startDate) : undefined}
            onChange={(value) => setStartDate(formatDate(value as Date))}
            maxDate={endDate ? new Date(endDate) : undefined}
          />
          <Calendar
            value={endDate ? createDateLocalTimezone(endDate) : undefined}
            onChange={(value) => setEndDate(formatDate(value as Date))}
            minDate={startDate ? new Date(startDate) : undefined}
          />
        </Box>
      </Container>
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
          onClick={() => {
            filter.setState([
              createDateLocalTimezone(startDate).getTime(),
              createDateLocalTimezone(endDate).getTime(),
            ]);
            setIsOpen(false);
          }}
        >
          Apply
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

function formatDate(date: Date) {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-based, so we need to add 1
  const dd = String(date.getDate()).padStart(2, '0');

  return `${yyyy}-${mm}-${dd}`;
}

const Container = styled.div`
  /* Hide the default date picker for Chrome, Edge, and Safari */
  input[type='date']::-webkit-calendar-picker-indicator {
    display: none;
  }

  /* Hide the default date picker for Firefox */
  input[type='date']::-moz-calendar-picker-indicator {
    display: none;
  }

  /* Hide the default date picker for Internet Explorer */
  input[type='date']::-ms-calendar-picker-indicator {
    display: none;
  }
`;

function createDateLocalTimezone(dateString) {
  const [year, month, day] = dateString.split('-');
  return new Date(year, month - 1, day);
}
