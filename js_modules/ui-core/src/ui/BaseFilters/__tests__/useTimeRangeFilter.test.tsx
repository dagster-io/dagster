import {IconName} from '@dagster-io/ui-components';
import {TZDate} from '@date-fns/tz';
import {render, waitFor} from '@testing-library/react';
import {renderHook} from '@testing-library/react-hooks';
import userEvent from '@testing-library/user-event';
import {endOfDay, startOfDay, subDays} from 'date-fns';
import {act, useState} from 'react';

import {TimeContext} from '../../../app/time/TimeContext';
import {DateRangeDialog} from '../../DateRangeDialog';
import {
  ActiveFilterState,
  TimeRangeState,
  calculateTimeRanges,
  useTimeRangeFilter,
} from '../useTimeRangeFilter';

const MAR_1_2025_MIDNIGHT_EASTERN = 1740805200000;
const MAR_3_2025_MIDNIGHT_EASTERN = 1740978000000;
const MAR_3_2025_END_OF_DAY_EASTERN = 1741064399999;

const MAR_1_2025_MIDNIGHT_DARWIN = 1740753000000;
const MAR_3_2025_MIDNIGHT_DARWIN = 1740925800000;
const MAR_3_2025_END_OF_DAY_DARWIN = 1741012199999;

jest.mock('@dagster-io/ui-components', () => ({
  ...jest.requireActual('@dagster-io/ui-components'),
  DayPickerWrapper: ({onSelect}: any) => {
    return (
      <div>
        <button
          onClick={() => {
            onSelect({
              from: new Date(MAR_1_2025_MIDNIGHT_EASTERN),
              to: new Date(MAR_3_2025_MIDNIGHT_EASTERN),
            });
          }}
        >
          Set NYC dates
        </button>
        <button
          onClick={() => {
            onSelect({
              from: new Date(MAR_1_2025_MIDNIGHT_DARWIN),
              to: new Date(MAR_3_2025_MIDNIGHT_DARWIN),
            });
          }}
        >
          Set Darwin dates
        </button>
      </div>
    );
  },
}));

const mockFilterProps = {
  name: 'Test Filter',
  activeFilterTerm: 'Timestamp',
  icon: 'date' as IconName,
};

function useTimeRangeFilterWrapper({state: initialState}: {state: TimeRangeState}) {
  const [state, setState] = useState<TimeRangeState>(initialState);
  return useTimeRangeFilter({...mockFilterProps, state, onStateChanged: setState});
}

describe('useTimeRangeFilter', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize filter state', () => {
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [2, 3]}));
    const filter = result.current;

    expect(filter.name).toBe(mockFilterProps.name);
    expect(filter.icon).toBe(mockFilterProps.icon);
    expect(filter.state).toEqual([2, 3]);
  });

  it('should reset filter state', () => {
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [1, 2]}));
    let filter = result.current;

    act(() => {
      filter.setState([Date.now(), Date.now()]);
    });

    filter = result.current;
    expect(filter.state).not.toEqual([1, 2]);

    act(() => {
      filter.setState([null, null]);
    });
    filter = result.current;

    expect(filter.state).toEqual([null, null]);
  });

  it('should handle pre-defined time ranges', () => {
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [null, null]}));
    let filter = result.current;

    act(() => {
      filter.onSelect({
        value: 'YESTERDAY',
        close: () => {},
        createPortal: () => () => {},
        clearSearch: () => {},
      });
    });
    filter = result.current;

    const {timeRanges} = calculateTimeRanges('UTC');
    expect(filter.state).toEqual(timeRanges.YESTERDAY.range);
  });
});

describe('DateRangeDialog', () => {
  it('should render', () => {
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [null, null]}));
    const filter = result.current;

    const {getByText} = render(
      <DateRangeDialog onApply={filter.setState} onCancel={() => {}} isOpen={true} />,
    );

    expect(getByText('Select a date range')).toBeInTheDocument();
  });

  it('should apply custom date range', async () => {
    const user = userEvent.setup();
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [null, null]}));

    const {findByText} = render(
      <TimeContext.Provider
        value={{
          timezone: ['America/New_York', () => {}, () => {}],
          resolvedTimezone: 'America/New_York',
          hourCycle: ['h23', () => {}, () => {}],
        }}
      >
        <DateRangeDialog onApply={result.current.setState} onCancel={() => {}} isOpen={true} />
      </TimeContext.Provider>,
    );

    const setDatesButton = await findByText(/set nyc dates/i);
    await user.click(setDatesButton);

    const applyButton = await findByText(/apply/i);
    await user.click(applyButton);

    const expectedStart = startOfDay(
      new TZDate(MAR_1_2025_MIDNIGHT_EASTERN, 'America/New_York'),
    ).valueOf();
    const expectedEnd = endOfDay(
      new TZDate(MAR_3_2025_END_OF_DAY_EASTERN, 'America/New_York'),
    ).valueOf();

    expect(result.current.state).toEqual([expectedStart, expectedEnd]);
  });

  it('should apply custom date range with timezone', async () => {
    const user = userEvent.setup();
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [null, null]}));

    const {findByText} = render(
      <TimeContext.Provider
        value={{
          timezone: ['Australia/Darwin', () => {}, () => {}],
          resolvedTimezone: 'Australia/Darwin',
          hourCycle: ['h23', () => {}, () => {}],
        }}
      >
        <DateRangeDialog onApply={result.current.setState} onCancel={() => {}} isOpen={true} />
      </TimeContext.Provider>,
    );

    const setDatesButton = await findByText(/set darwin dates/i);
    await user.click(setDatesButton);

    const applyButton = await findByText(/apply/i);
    await user.click(applyButton);

    const expectedStart = startOfDay(
      new TZDate(MAR_1_2025_MIDNIGHT_DARWIN, 'Australia/Darwin'),
    ).valueOf();
    const expectedEnd = endOfDay(
      new TZDate(MAR_3_2025_END_OF_DAY_DARWIN, 'Australia/Darwin'),
    ).valueOf();

    expect(result.current.state).toEqual([expectedStart, expectedEnd]);
  });

  it('should close dialog on cancel', async () => {
    const closeMock = jest.fn();
    const {result} = await act(async () =>
      renderHook(() => useTimeRangeFilterWrapper({state: [null, null]})),
    );
    let filter = result.current;

    const {getByText} = render(
      <DateRangeDialog
        onApply={(val) => {
          filter.setState(val);
          closeMock();
        }}
        onCancel={closeMock}
        isOpen={true}
      />,
    );

    // Click cancel button
    await userEvent.click(getByText('Cancel'));
    filter = result.current;

    await waitFor(() => {
      // wait for blueprint animation
      expect(closeMock).toHaveBeenCalled();
    });
  });
});

describe('ActiveFilterState', () => {
  const mockTimezone = 'UTC';
  const {timeRanges} = calculateTimeRanges(mockTimezone);
  const removeMock = jest.fn();

  afterEach(() => {
    removeMock.mockClear();
  });

  it('should render Today filter state', () => {
    const {getByText} = render(
      <ActiveFilterState
        activeFilterTerm="Timestamp"
        state={timeRanges.TODAY.range}
        remove={removeMock}
        timezone={mockTimezone}
        timeRanges={timeRanges}
      />,
    );

    expect(getByText(/Today/)).toBeInTheDocument();
  });

  it('should render Yesterday filter state', () => {
    const {getByText} = render(
      <ActiveFilterState
        activeFilterTerm="Timestamp"
        state={timeRanges.YESTERDAY.range}
        remove={removeMock}
        timezone={mockTimezone}
        timeRanges={timeRanges}
      />,
    );

    expect(getByText(/Yesterday/)).toBeInTheDocument();
  });

  it('should render Within last 7 days filter state', () => {
    const {getByText} = render(
      <ActiveFilterState
        activeFilterTerm="Timestamp"
        state={timeRanges.LAST_7_DAYS.range}
        remove={removeMock}
        timezone={mockTimezone}
        timeRanges={timeRanges}
      />,
    );

    expect(getByText(/Last 7 days/i)).toBeInTheDocument();
  });

  it('should render Within last 30 days filter state', () => {
    const {getByText} = render(
      <ActiveFilterState
        activeFilterTerm="Timestamp"
        state={timeRanges.LAST_30_DAYS.range}
        remove={removeMock}
        timezone={mockTimezone}
        timeRanges={timeRanges}
      />,
    );

    expect(getByText(/Last 30 days/i)).toBeInTheDocument();
  });

  it('should render custom filter state with lower boundary', () => {
    const customRange = [subDays(new Date(), 3).valueOf(), null] as TimeRangeState;
    const {getByText} = render(
      <ActiveFilterState
        activeFilterTerm="Timestamp"
        state={customRange}
        remove={removeMock}
        timezone={mockTimezone}
        timeRanges={timeRanges}
      />,
    );

    expect(getByText(/Timestamp after/)).toBeInTheDocument();
  });

  it('should render custom filter state with upper boundary', () => {
    const customRange = [null, subDays(new Date(), 1).valueOf()] as TimeRangeState;
    const {getByText} = render(
      <ActiveFilterState
        activeFilterTerm="Timestamp"
        state={customRange}
        remove={removeMock}
        timezone={mockTimezone}
        timeRanges={timeRanges}
      />,
    );

    expect(getByText(/Timestamp before/)).toBeInTheDocument();
  });

  it('should render custom filter state with both boundaries', () => {
    const customRange = [
      subDays(new Date(), 5).valueOf(),
      subDays(new Date(), 2).valueOf(),
    ] as TimeRangeState;
    const {getByText} = render(
      <ActiveFilterState
        activeFilterTerm="Timestamp"
        state={customRange}
        remove={removeMock}
        timezone={mockTimezone}
        timeRanges={timeRanges}
      />,
    );

    expect(getByText(/Timestamp from/)).toBeInTheDocument();
  });
});
