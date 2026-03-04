import {act, renderHook} from '@testing-library/react-hooks';
import {useState} from 'react';

import {useThrottledEffect} from '../useThrottledEffect';

// Mock timer functions
jest.useFakeTimers();

describe('useThrottledEffect', () => {
  beforeEach(() => {
    jest.clearAllTimers();
    jest.clearAllMocks();
  });

  test('should run effect immediately on first render', () => {
    const callback = jest.fn();
    renderHook(() => useThrottledEffect(callback, [1], 1000));

    expect(callback).toHaveBeenCalledTimes(1);
  });

  test('should not run effect again if dependencies change within delay time', () => {
    const callback = jest.fn();
    const {rerender} = renderHook(({dep}) => useThrottledEffect(callback, [dep], 1000), {
      initialProps: {dep: 1},
    });

    expect(callback).toHaveBeenCalledTimes(1);

    // Change dependency but don't advance timer
    rerender({dep: 2});

    // Effect should not have been called again yet
    expect(callback).toHaveBeenCalledTimes(1);
  });

  test('should run effect after delay time has passed', () => {
    const callback = jest.fn();
    const {rerender} = renderHook(({dep}) => useThrottledEffect(callback, [dep], 1000), {
      initialProps: {dep: 1},
    });

    expect(callback).toHaveBeenCalledTimes(1);

    // Change dependency
    rerender({dep: 2});

    // Advance timer past the delay
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    // Effect should now have been called again
    expect(callback).toHaveBeenCalledTimes(2);
  });

  test('should handle multiple rapid dependency changes', () => {
    const callback = jest.fn();
    const {rerender} = renderHook(({dep}) => useThrottledEffect(callback, [dep], 1000), {
      initialProps: {dep: 1},
    });

    expect(callback).toHaveBeenCalledTimes(1);

    // Multiple rapid changes
    rerender({dep: 2});
    rerender({dep: 3});
    rerender({dep: 4});

    // Effect should still have only been called once
    expect(callback).toHaveBeenCalledTimes(1);

    // Advance timer past the delay
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    // Effect should now have been called again (with the latest dependency value)
    expect(callback).toHaveBeenCalledTimes(2);
  });

  test('should run immediately if dependency changes after delay has passed', () => {
    const callback = jest.fn();
    const {rerender} = renderHook(({dep}) => useThrottledEffect(callback, [dep], 1000), {
      initialProps: {dep: 1},
    });

    expect(callback).toHaveBeenCalledTimes(1);

    // Advance timer past the delay
    act(() => {
      jest.advanceTimersByTime(1500);
    });

    // Change dependency after delay has passed
    rerender({dep: 2});

    // Effect should run immediately
    expect(callback).toHaveBeenCalledTimes(2);
  });

  test('should clean up timeout on unmount', () => {
    const callback = jest.fn();
    const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');

    const {rerender, unmount} = renderHook(({dep}) => useThrottledEffect(callback, [dep], 1000), {
      initialProps: {dep: 1},
    });

    // Trigger a throttled update
    rerender({dep: 2});

    // Unmount the component
    unmount();

    // Should have cleared the timeout
    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  test('should work with multiple dependencies', () => {
    const callback = jest.fn();
    const {rerender} = renderHook(({deps}) => useThrottledEffect(callback, deps, 1000), {
      initialProps: {deps: [1, 'a', true]},
    });

    expect(callback).toHaveBeenCalledTimes(1);

    // Change only one dependency
    rerender({deps: [1, 'b', true]});

    // Advance timer past the delay
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    // Effect should have been called again
    expect(callback).toHaveBeenCalledTimes(2);
  });

  test('should work correctly in a component with state updates', () => {
    const callback = jest.fn();

    // Create a test component with state
    const TestHook = ({delay}: {delay: number}) => {
      const [count, setCount] = useState(0);

      useThrottledEffect(
        () => {
          callback(count);
        },
        [count],
        delay,
      );

      return {setCount};
    };

    const {result} = renderHook(() => TestHook({delay: 1000}));

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenLastCalledWith(0);

    // Update state multiple times rapidly
    act(() => {
      result.current.setCount(1);
      result.current.setCount(2);
      result.current.setCount(3);
    });

    // Effect should not have been called again yet
    expect(callback).toHaveBeenCalledTimes(1);

    // Advance timer past the delay
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    // Effect should have been called with the latest state
    expect(callback).toHaveBeenCalledTimes(2);
    expect(callback).toHaveBeenLastCalledWith(3);
  });

  test('should call cleanup function when dependencies change', () => {
    const cleanup = jest.fn();
    const callback = jest.fn().mockReturnValue(cleanup);

    const {rerender} = renderHook(({dep}) => useThrottledEffect(callback, [dep], 1000), {
      initialProps: {dep: 1},
    });

    expect(callback).toHaveBeenCalledTimes(1);
    expect(cleanup).not.toHaveBeenCalled();

    // Advance timer and change dependency
    act(() => {
      jest.advanceTimersByTime(1500);
    });
    rerender({dep: 2});

    // Cleanup should have been called before the next effect
    expect(cleanup).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledTimes(2);
  });

  test('should call cleanup function on unmount', () => {
    const cleanup = jest.fn();
    const callback = jest.fn().mockReturnValue(cleanup);

    const {unmount} = renderHook(() => useThrottledEffect(callback, [1], 1000));

    expect(callback).toHaveBeenCalledTimes(1);
    expect(cleanup).not.toHaveBeenCalled();

    // Unmount the component
    unmount();

    // Cleanup should have been called
    expect(cleanup).toHaveBeenCalledTimes(1);
  });

  test('should call previous cleanup before running new effect', () => {
    const cleanupA = jest.fn();
    const cleanupB = jest.fn();
    const callback = jest
      .fn()
      .mockImplementationOnce(() => cleanupA)
      .mockImplementationOnce(() => cleanupB);

    const {rerender, unmount} = renderHook(({dep}) => useThrottledEffect(callback, [dep], 1000), {
      initialProps: {dep: 1},
    });

    expect(callback).toHaveBeenCalledTimes(1);
    expect(cleanupA).not.toHaveBeenCalled();

    // Advance timer and change dependency
    act(() => {
      jest.advanceTimersByTime(1500);
    });
    rerender({dep: 2});

    // First cleanup should be called before second effect runs
    expect(cleanupA).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledTimes(2);
    expect(cleanupB).not.toHaveBeenCalled();

    // Unmount to test second cleanup
    unmount();
    expect(cleanupB).toHaveBeenCalledTimes(1);
  });

  test('should handle case when effect does not return cleanup function', () => {
    // First call returns cleanup, second doesn't
    const cleanup = jest.fn();
    const callback = jest
      .fn()
      .mockImplementationOnce(() => cleanup)
      .mockImplementationOnce(() => undefined);

    const {rerender, unmount} = renderHook(({dep}) => useThrottledEffect(callback, [dep], 1000), {
      initialProps: {dep: 1},
    });

    // Advance timer and change dependency
    act(() => {
      jest.advanceTimersByTime(1500);
    });
    rerender({dep: 2});

    // Should have called cleanup from first effect
    expect(cleanup).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledTimes(2);

    // Unmount should not error even though second effect had no cleanup
    expect(() => unmount()).not.toThrow();
  });
});
