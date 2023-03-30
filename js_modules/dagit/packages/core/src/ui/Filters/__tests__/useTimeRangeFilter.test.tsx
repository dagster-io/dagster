import {IconName} from '@dagster-io/ui';
import {render, fireEvent, act, waitFor} from '@testing-library/react';
import {renderHook} from '@testing-library/react-hooks';
// eslint-disable-next-line no-restricted-imports
import moment from 'moment-timezone';
import React from 'react';

import {
  calculateTimeRanges,
  useTimeRangeFilter,
  CustomTimeRangeFilterDialog,
  TimeRangeState,
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
  icon: 'date' as IconName,
  timezone: 'UTC',
  initialState: [null, null] as TimeRangeState,
};

describe('useTimeRangeFilter', () => {
  it('should initialize filter state', () => {
    const {result} = renderHook(() => useTimeRangeFilter(mockFilterProps));
    const filter = result.current;

    expect(filter.name).toBe(mockFilterProps.name);
    expect(filter.icon).toBe(mockFilterProps.icon);
    expect(filter.state).toEqual(mockFilterProps.initialState);
  });

  it('should reset filter state', () => {
    const {result} = renderHook(() => useTimeRangeFilter(mockFilterProps));
    let filter = result.current;

    act(() => {
      filter.setState([Date.now(), Date.now()]);
    });

    filter = result.current;
    expect(filter.state).not.toEqual(mockFilterProps.initialState);

    act(() => {
      filter.setState([null, null]);
    });
    filter = result.current;

    expect(filter.state).toEqual(mockFilterProps.initialState);
  });

  it('should handle pre-defined time ranges', () => {
    const {result} = renderHook(() => useTimeRangeFilter(mockFilterProps));
    let filter = result.current;

    act(() => {
      filter.onSelect({value: 'YESTERDAY', close: () => {}, createPortal: () => () => {}});
    });
    filter = result.current;

    const {timeRanges} = calculateTimeRanges(mockFilterProps.timezone);
    expect(filter.state).toEqual(timeRanges.YESTERDAY.range);
  });
});

describe('CustomTimeRangeFilterDialog', () => {
  it('should render', () => {
    const {result} = renderHook(() => useTimeRangeFilter(mockFilterProps));
    const filter = result.current;

    const {getByText} = render(
      <CustomTimeRangeFilterDialog filter={filter} closeRef={{current: () => {}}} />,
    );

    expect(getByText('Select a date range')).toBeInTheDocument();
  });

  it('should apply custom date range', () => {
    const {result} = renderHook(() => useTimeRangeFilter(mockFilterProps));
    let filter = result.current;

    const {getByText} = render(
      <CustomTimeRangeFilterDialog filter={filter} closeRef={{current: () => {}}} />,
    );

    // Mock selecting start and end dates
    const startDate = moment().subtract(10, 'days');
    const endDate = moment().subtract(5, 'days');

    act(() => {
      ((mockReactDates.mock.calls[0] as any)[0] as any).onDatesChange({
        startDate,
        endDate,
      });
    });

    // Click apply button
    fireEvent.click(getByText('Apply'));
    filter = result.current;

    expect(filter.state).toEqual([startDate.valueOf(), endDate.valueOf()]);
  });

  it('should close dialog on cancel', async () => {
    const closeRefMock = jest.fn();
    const {result} = renderHook(() => useTimeRangeFilter(mockFilterProps));
    let filter = result.current;

    const {getByText} = render(
      <CustomTimeRangeFilterDialog filter={filter} closeRef={{current: closeRefMock}} />,
    );

    // Click cancel button
    fireEvent.click(getByText('Cancel'));
    filter = result.current;

    await waitFor(() => {
      // wait for blueprint animation
      expect(closeRefMock).toHaveBeenCalled();
    });
  });
});
