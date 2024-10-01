import {renderHook} from '@testing-library/react-hooks';

import {usePredicateChangeSignal} from '../usePredicateChangeSignal';

describe('usePredicateChangeSignal', () => {
  it('should alternate between 0 and 1 when the predicate signals a change', () => {
    const predicate = jest.fn((prev, curr) => {
      return !prev || prev[0] !== curr[0];
    });

    const {result, rerender} = renderHook(({deps}) => usePredicateChangeSignal(predicate, deps), {
      initialProps: {deps: [1]},
    });

    expect(result.current).toBe(0);
    expect(predicate).toHaveBeenCalledWith(null, [1]);

    rerender({deps: [2]});
    expect(result.current).toBe(1);
    expect(predicate).toHaveBeenCalledWith([1], [2]);

    rerender({deps: [3]});
    expect(result.current).toBe(0);
    expect(predicate).toHaveBeenCalledWith([2], [3]);
  });

  it('should not change the value if the predicate does not signal a change', () => {
    const predicate = jest.fn((prev, curr) => {
      return !prev || prev[0] !== curr[0];
    });

    const {result, rerender} = renderHook(({deps}) => usePredicateChangeSignal(predicate, deps), {
      initialProps: {deps: [1]},
    });

    expect(result.current).toBe(0);
    expect(predicate).toHaveBeenCalledWith(null, [1]);

    rerender({deps: [1]});
    expect(result.current).toBe(0); // No change since deps are the same
    expect(predicate).toHaveBeenCalledWith(null, [1]);
  });
});
