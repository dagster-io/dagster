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

    expect(result.current).toEqual(firstObject);

    rerender({value: secondObject});

    const firstResult = result.current;
    rerender({value: secondObject});
    expect(result.current).toBe(firstResult);
  });
});
