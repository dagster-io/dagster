import {renderHook} from '@testing-library/react-hooks';

import {useStableReferenceByHash} from '../useStableReferenceByHash';

describe('useStableReferenceByHash', () => {
  it('should return the same value for the same input', () => {
    const aValue = {a: 1};
    const aValue2 = {a: 1};
    const {result: aResult} = renderHook(() => useStableReferenceByHash(aValue, true));
    const {result: aResult2} = renderHook(() => useStableReferenceByHash(aValue2, true));

    expect(aResult.current).toBe(aValue);
    expect(aResult2.current).toBe(aValue);
  });
});
