import {IconName} from '@dagster-io/ui-components';
import {act, render, waitFor} from '@testing-library/react';
import {renderHook} from '@testing-library/react-hooks';
import userEvent from '@testing-library/user-event';
// eslint-disable-next-line no-restricted-imports
import moment from 'moment-timezone';
import {useState} from 'react';

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
  it('should render', () => {
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [null, null]}));
    const filter = result.current;

    const {getByText} = render(<CustomTimeRangeFilterDialog filter={filter} close={() => {}} />);

    expect(getByText('Select a date range')).toBeInTheDocument();
  });

  it('should apply custom date range', async () => {
    const {result} = renderHook(() => useTimeRangeFilterWrapper({state: [null, null]}));
    let filter = result.current;

    const {getByText} = await act(async () =>
      render(<CustomTimeRangeFilterDialog filter={filter} close={() => {}} />),
    );

    // Mock selecting start and end dates
    const startDate = moment().startOf('day').subtract(10, 'days');
    const endDate = moment().endOf('day').subtract(5, 'days');

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

    expect(filter.state).toEqual([startDate.valueOf(), endDate.valueOf()]);
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
