import {IconName} from '@dagster-io/ui-components';
import {act, render, waitFor} from '@testing-library/react';
import {renderHook} from '@testing-library/react-hooks';
import userEvent from '@testing-library/user-event';
// eslint-disable-next-line no-restricted-imports
import moment from 'moment-timezone';
import {useState} from 'react';

import {TimeContext} from '../../../app/time/TimeContext';
import {
  ActiveFilterState,
  CustomTimeRangeFilterDialog,
  TimeRangeState,
  calculateTimeRanges,
  useTimeRangeFilter,
} from '../useTimeRangeFilter';

let mockReactDates = jest.fn((_props) => <div />);
beforeEach(() => {
  mockReactDates = jest.fn((_props) => <div />);
});
jest.mock('react-dates', () => {
  return {
    DateRangePicker: (props: any) => mockReactDates(props),
  };
});
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

describe('CustomTimeRangeFilterDialog', () => {
  const MAR_1_2025_MIDNIGHT_EASTERN = 1740805200000;
  const MAR_3_2025_MIDNIGHT_CENTRAL = 1740978000000;
  const MAR_3_2025_END_OF_DAY_EASTERN = 1740985599000;

  const MAR_1_2025_MIDNIGHT_DARWIN = 1740753000000;
  const MAR_3_2025_MIDNIGHT_DARWIN = 1740925800000;
  const MAR_3_2025_END_OF_DAY_DARWIN = 1741012140000;

  it('should render', () => {
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [null, null]}));
    const filter = result.current;

    const {getByText} = render(<CustomTimeRangeFilterDialog filter={filter} close={() => {}} />);

    expect(getByText('Select a date range')).toBeInTheDocument();
  });

  it('should apply custom date range', async () => {
    const user = userEvent.setup();
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [null, null]}));
    let filter = result.current;
    const originalDefaultTimezone = moment.tz.guess();
    moment.tz.setDefault('America/New_York');

    const {getByText} = await act(async () =>
      render(
        <TimeContext.Provider
          value={{
            timezone: ['America/New_York', () => {}, () => {}],
            hourCycle: ['h23', () => {}, () => {}],
          }}
        >
          <CustomTimeRangeFilterDialog filter={filter} close={() => {}} />
        </TimeContext.Provider>,
      ),
    );

    // Mock selecting start and end dates
    const startDate = moment(MAR_1_2025_MIDNIGHT_EASTERN);
    const endDate = moment(MAR_3_2025_MIDNIGHT_CENTRAL);

    await waitFor(() => {
      act(() => {
        ((mockReactDates.mock.calls[0] as any)[0] as any).onDatesChange({
          startDate,
          endDate,
        });
      });
    });

    // Click apply button
    await user.click(getByText('Apply'));
    filter = result.current;

    const expectedStart = moment
      .tz(MAR_1_2025_MIDNIGHT_EASTERN, 'America/New_York')
      .startOf('day')
      .valueOf();
    const expectedEnd = moment
      .tz(MAR_3_2025_END_OF_DAY_EASTERN, 'America/New_York')
      .endOf('day')
      .valueOf();

    expect(filter.state).toEqual([expectedStart, expectedEnd]);
    moment.tz.setDefault(originalDefaultTimezone);
  });

  it('should apply custom date range with timezone', async () => {
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [null, null]}));
    let filter = result.current;
    const originalDefaultTimezone = moment.tz.guess();
    moment.tz.setDefault('Australia/Darwin');

    const {getByText} = await act(async () =>
      render(
        <TimeContext.Provider
          value={{
            timezone: ['Australia/Darwin', () => {}, () => {}],
            hourCycle: ['h23', () => {}, () => {}],
          }}
        >
          <CustomTimeRangeFilterDialog filter={filter} close={() => {}} />
        </TimeContext.Provider>,
      ),
    );

    // Mock selecting start and end dates
    const startDate = moment(MAR_1_2025_MIDNIGHT_DARWIN);
    const endDate = moment(MAR_3_2025_MIDNIGHT_DARWIN);

    await waitFor(() => {
      act(() => {
        ((mockReactDates.mock.calls[0] as any)[0] as any).onDatesChange({
          startDate,
          endDate,
        });
      });
    });

    // Click apply button
    await userEvent.click(getByText('Apply'));
    filter = result.current;

    const expectedStart = moment
      .tz(MAR_1_2025_MIDNIGHT_DARWIN, 'Australia/Darwin')
      .startOf('day')
      .valueOf();
    const expectedEnd = moment
      .tz(MAR_3_2025_END_OF_DAY_DARWIN, 'Australia/Darwin')
      .endOf('day')
      .valueOf();

    expect(filter.state).toEqual([expectedStart, expectedEnd]);
    moment.tz.setDefault(originalDefaultTimezone);
  });

  it('should apply custom date range with timezone even when browser has other default', async () => {
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [null, null]}));
    let filter = result.current;
    const originalDefaultTimezone = moment.tz.guess();
    moment.tz.setDefault('America/New_York');

    const {getByText} = await act(async () =>
      render(
        <TimeContext.Provider
          value={{
            timezone: ['Australia/Darwin', () => {}, () => {}],
            hourCycle: ['h23', () => {}, () => {}],
          }}
        >
          <CustomTimeRangeFilterDialog filter={filter} close={() => {}} />
        </TimeContext.Provider>,
      ),
    );

    // Mock selecting start and end dates
    const startDate = moment(MAR_1_2025_MIDNIGHT_EASTERN);
    const endDate = moment(MAR_3_2025_MIDNIGHT_CENTRAL);

    await waitFor(() => {
      act(() => {
        ((mockReactDates.mock.calls[0] as any)[0] as any).onDatesChange({
          startDate,
          endDate,
        });
      });
    });

    // Click apply button
    await userEvent.click(getByText('Apply'));
    filter = result.current;

    const expectedStart = moment
      .tz(MAR_1_2025_MIDNIGHT_DARWIN, 'Australia/Darwin')
      .startOf('day')
      .valueOf();
    const expectedEnd = moment
      .tz(MAR_3_2025_END_OF_DAY_DARWIN, 'Australia/Darwin')
      .endOf('day')
      .valueOf();

    expect(filter.state).toEqual([expectedStart, expectedEnd]);
    moment.tz.setDefault(originalDefaultTimezone);
  });

  it('should close dialog on cancel', async () => {
    const closeMock = jest.fn();
    const {result} = await act(async () =>
      renderHook(() => useTimeRangeFilterWrapper({state: [null, null]})),
    );
    let filter = result.current;

    const {getByText} = render(<CustomTimeRangeFilterDialog filter={filter} close={closeMock} />);

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
    const customRange = [moment().subtract(3, 'days').valueOf(), null] as TimeRangeState;
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
    const customRange = [null, moment().subtract(1, 'days').valueOf()] as TimeRangeState;
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
      moment().subtract(5, 'days').valueOf(),
      moment().subtract(2, 'days').valueOf(),
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
