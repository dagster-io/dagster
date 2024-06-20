import {act, renderHook} from '@testing-library/react-hooks';

import {useThrottledMemo} from '../useThrottledMemo';

jest.useFakeTimers();

describe('useThrottledMemo', () => {
  it('should compute the memoized value immediately on mount', () => {
    const factory = jest.fn(() => 42);
    const {result} = renderHook(() => useThrottledMemo(factory, [], 1000));

    expect(result.current).toBe(42);
    expect(factory).toHaveBeenCalledTimes(1);
  });

  it('should recompute the memoized value after the delay', () => {
    let value = 1;
    const factory = jest.fn(() => value);
    const {result, rerender} = renderHook(() => useThrottledMemo(factory, [value], 1000));

    expect(result.current).toBe(1);
    expect(factory).toHaveBeenCalledTimes(1);

    value = 2;
    rerender();

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(result.current).toBe(2);
    expect(factory).toHaveBeenCalledTimes(2);
  });

  it('should not recompute the memoized value if delay has not passed', () => {
    let value = 1;
    const factory = jest.fn(() => value);
    const {result, rerender} = renderHook(() => useThrottledMemo(factory, [value], 1000));

    expect(result.current).toBe(1);
    expect(factory).toHaveBeenCalledTimes(1);

    value = 2;
    rerender();

    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(result.current).toBe(1);
    expect(factory).toHaveBeenCalledTimes(1);

    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(result.current).toBe(2);
    expect(factory).toHaveBeenCalledTimes(2);
  });

  it('should cancel the timeout when the component unmounts', () => {
    const factory = jest.fn(() => 42);
    const {unmount} = renderHook(() => useThrottledMemo(factory, [], 1000));

    unmount();

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(factory).toHaveBeenCalledTimes(1); // Only the initial call
  });

  it('should use the latest value when recomputing', () => {
    let value = 1;
    const factory = jest.fn(() => value);
    const {result, rerender} = renderHook(() => useThrottledMemo(factory, [value], 1000));

    expect(result.current).toBe(1);
    expect(factory).toHaveBeenCalledTimes(1);

    value = 2;
    rerender();

    act(() => {
      jest.advanceTimersByTime(500);
    });

    value = 3;
    rerender();

    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(result.current).toBe(3);
    expect(factory).toHaveBeenCalledTimes(2);
  });
});
