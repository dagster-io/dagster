import {renderHook} from '@testing-library/react-hooks';

import {useStableReferenceByHash} from '../useStableReferenceByHash';

describe('useStableReferenceByHash', () => {
  it('should maintain separate references for different hook instances', () => {
    // Create two objects with the same content
    const firstObject = {a: 1};
    const secondObject = {a: 1};

    const {result, rerender} = renderHook(({value}) => useStableReferenceByHash(value), {
      initialProps: {value: firstObject},
    });

    // Each hook should maintain its own reference
    expect(result.current).toEqual(firstObject);

    // Test that references remain stable even when props change
    rerender({value: secondObject});

    expect(result.current).toEqual(firstObject);
  });
});
