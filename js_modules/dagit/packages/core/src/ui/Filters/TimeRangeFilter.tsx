import {IconName, Box, Icon, Colors, Dialog, Button, DialogFooter} from '@dagster-io/ui';
import dayjs from 'dayjs';
import isEqual from 'lodash/isEqual';
// eslint-disable-next-line no-restricted-imports
import moment from 'moment';
import React from 'react';
import {DateRangePicker} from 'react-dates';
import styled from 'styled-components/macro';

import {Filter, FilterTag, FilterTagHighlightedText} from './Filter';

import 'react-dates/initialize';
import 'react-dates/lib/css/_datepicker.css';

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
    close: () => void,
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
    close();
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
  const [startDate, setStartDate] = React.useState<moment.Moment | null>(null);
  const [endDate, setEndDate] = React.useState<moment.Moment | null>(null);
  const [focusedInput, setFocusedInput] = React.useState<'startDate' | 'endDate'>('startDate');

  const [isOpen, setIsOpen] = React.useState(true);

  return (
    <Dialog
      isOpen={isOpen}
      title="Select a date range"
      onClosed={() => {
        // close the portal after the animation is done
        closeRef.current();
      }}
      style={{width: '652px'}}
    >
      <Container>
        <Box flex={{direction: 'row', gap: 8}} padding={16}>
          <DateRangePicker
            onDatesChange={({startDate, endDate}) => {
              setStartDate(startDate);
              setEndDate(endDate);
            }}
            onFocusChange={(focusedInput) => {
              focusedInput && setFocusedInput(focusedInput);
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

const Container = styled.div`
  height: 430px;

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

  .DayPickerKeyboardShortcuts_show {
    display: none;
  }

  .CalendarDay__hovered_span,
  .CalendarDay__hovered_span:hover,
  .CalendarDay__selected_span,
  .CalendarDay__selected_span:hover {
    background: ${Colors.Blue50};
    color: ${Colors.Blue700};
    border: 1px solid #e4e7e7;
  }
  .CalendarDay__selected,
  .CalendarDay__selected:active,
  .CalendarDay__selected:hover {
    background: ${Colors.Blue200};
    border: 1px solid #e4e7e7;
  }
  .DateInput_input__focused {
    border-color: ${Colors.Blue500};
  }
`;

function createDateLocalTimezone(dateString: string) {
  const [year, month, day] = dateString.split('-');
  return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
}
