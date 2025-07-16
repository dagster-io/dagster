import {renderHook} from '@testing-library/react-hooks';

import {useStableReferenceByHash} from '../useStableReferenceByHash';

describe('useStableReferenceByHash', () => {
  it('should maintain separate references for different hook instances', () => {
    // Create two objects with the same content
    const firstObject = {a: 1};
    const secondObject = {a: 1}; // Same content as firstObject

    // Create two separate hook instances with storeInMap=false
    const {result: firstResult, rerender: firstRerender} = renderHook(
      ({value}) => useStableReferenceByHash(value),
      {initialProps: {value: firstObject}},
    );
    const {result: secondResult, rerender: secondRerender} = renderHook(
      ({value}) => useStableReferenceByHash(value),
      {initialProps: {value: secondObject}},
    );

    // Each hook should maintain its own reference
    expect(firstResult.current).toEqual(firstObject);
    expect(secondResult.current).toEqual(secondObject);

    // Test that references remain stable even when props change
    firstRerender({value: secondObject});
    secondRerender({value: firstObject});

    // Each hook should maintain its original reference
    // This demonstrates that the hook preserves the initial reference
    // even when receiving new props
    expect(firstResult.current).toEqual(firstObject);
    expect(secondResult.current).toEqual(secondObject);
  });
});
