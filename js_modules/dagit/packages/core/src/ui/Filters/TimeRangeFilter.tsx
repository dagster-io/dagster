import {IconName, Box, Icon, Colors, Dialog, Button, DialogFooter, TextInput} from '@dagster-io/ui';
import dayjs from 'dayjs';
import isEqual from 'lodash/isEqual';
import React from 'react';
import Calendar from 'react-calendar';
import styled from 'styled-components/macro';

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
              if (endDate && new Date(endDate) <= new Date(e.target.value)) {
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
              if (startDate && new Date(startDate) >= new Date(e.target.value)) {
                setStartDate(e.target.value);
              }
            }}
          />
        </Box>
        <Box flex={{direction: 'row', gap: 8}} padding={16}>
          <Calendar
            value={startDate ? createDateLocalTimezone(startDate) : undefined}
            onChange={(value) => setStartDate(formatDate(value as Date))}
            maxDate={
              endDate ? new Date(createDateLocalTimezone(endDate).getTime() - MS_IN_DAY) : undefined
            }
          />
          <Calendar
            value={endDate ? createDateLocalTimezone(endDate) : undefined}
            onChange={(value) => setEndDate(formatDate(value as Date))}
            minDate={
              startDate
                ? new Date(createDateLocalTimezone(startDate).getTime() + MS_IN_DAY)
                : undefined
            }
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
          disabled={!startDate || !endDate}
          onClick={() => {
            filter.setState([
              createDateLocalTimezone(startDate!).getTime(),
              createDateLocalTimezone(endDate!).getTime(),
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

  .react-calendar {
    width: 350px;
    max-width: 100%;
    background: ${Colors.White};
    border: 1px solid ${Colors.Gray300};
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.125em;
  }

  .react-calendar--doubleView {
    width: 700px;
  }

  .react-calendar--doubleView .react-calendar__viewContainer {
    display: flex;
    margin: -0.5em;
  }

  .react-calendar--doubleView .react-calendar__viewContainer > * {
    width: 50%;
    margin: 0.5em;
  }

  .react-calendar,
  .react-calendar *,
  .react-calendar *:before,
  .react-calendar *:after {
    -moz-box-sizing: border-box;
    -webkit-box-sizing: border-box;
    box-sizing: border-box;
  }

  .react-calendar button {
    margin: 0;
    border: 0;
    outline: none;
  }

  .react-calendar button:enabled:hover {
    cursor: pointer;
  }

  .react-calendar__navigation {
    display: flex;
    height: 44px;
    margin-bottom: 1em;
  }

  .react-calendar__navigation button {
    min-width: 44px;
    background: none;
  }

  .react-calendar__navigation button:disabled {
    background-color: ${Colors.Gray200};
  }

  .react-calendar__navigation button:enabled:hover,
  .react-calendar__navigation button:enabled:focus {
    background-color: ${Colors.Gray300};
  }

  .react-calendar__month-view__weekdays {
    text-align: center;
    text-transform: uppercase;
    font-weight: bold;
    font-size: 0.75em;
  }

  .react-calendar__month-view__weekdays__weekday {
    padding: 0.5em;
  }

  .react-calendar__month-view__weekNumbers .react-calendar__tile {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75em;
    font-weight: bold;
  }

  .react-calendar__month-view__days__day--weekend {
  }

  .react-calendar__month-view__days__day--neighboringMonth {
    color: ${Colors.Gray500};
  }

  .react-calendar__year-view .react-calendar__tile,
  .react-calendar__decade-view .react-calendar__tile,
  .react-calendar__century-view .react-calendar__tile {
    padding: 2em 0.5em;
  }

  .react-calendar__tile {
    max-width: 100%;
    padding: 10px 6.6667px;
    background: none;
    text-align: center;
    line-height: 16px;
  }

  .react-calendar__tile:disabled {
    background-color: ${Colors.Gray200};
  }

  .react-calendar__tile:enabled:hover,
  .react-calendar__tile:enabled:focus {
    background-color: ${Colors.Gray300};
  }

  .react-calendar__tile--now {
    background: inherit;
  }

  .react-calendar__tile--now:enabled:hover,
  .react-calendar__tile--now:enabled:focus {
    background: ${Colors.Yellow500};
  }

  .react-calendar__tile--hasActive {
    background: ${Colors.Blue200};
  }

  .react-calendar__tile--hasActive:enabled:hover,
  .react-calendar__tile--hasActive:enabled:focus {
    background: ${Colors.Blue500};
  }

  .react-calendar__tile--active {
    background: ${Colors.Blue500};
    color: ${Colors.White};
  }

  .react-calendar__tile--active:enabled:hover,
  .react-calendar__tile--active:enabled:focus {
    background: ${Colors.Blue500};
  }

  .react-calendar--selectRange .react-calendar__tile--hover {
    background-color: ${Colors.Gray200};
  }
`;

function createDateLocalTimezone(dateString: string) {
  const [year, month, day] = dateString.split('-');
  return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
}

const MS_IN_DAY = 1000 * 60 * 60 * 24;
