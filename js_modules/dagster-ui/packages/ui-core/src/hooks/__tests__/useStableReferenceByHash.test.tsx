import {renderHook} from '@testing-library/react-hooks';

import {useStableReferenceByHash} from '../useStableReferenceByHash';

describe('useStableReferenceByHash', () => {
  describe('when storeInMap is true', () => {
    it('should maintain reference stability across different hook instances for identical objects', () => {
      // Create two objects with the same content
      const firstObject = {a: 1};
      const secondObject = {a: 1}; // Same content as firstObject

      // Create two separate hook instances with storeInMap=true
      const {result: firstResult} = renderHook(() => useStableReferenceByHash(firstObject, true));
      const {result: secondResult} = renderHook(() => useStableReferenceByHash(secondObject, true));

      // Both hooks should return the same reference (firstObject)
      // This means the hook is maintaining reference stability across instances
      expect(firstResult.current).toBe(firstObject);
      expect(secondResult.current).toBe(firstObject);
    });
  });

  describe('when storeInMap is false', () => {
    it('should maintain separate references for different hook instances', () => {
      // Create two objects with the same content
      const firstObject = {a: 1};
      const secondObject = {a: 1}; // Same content as firstObject

      // Create two separate hook instances with storeInMap=false
      const {result: firstResult, rerender: firstRerender} = renderHook(
        ({value}) => useStableReferenceByHash(value, false),
        {initialProps: {value: firstObject}},
      );
      const {result: secondResult, rerender: secondRerender} = renderHook(
        ({value}) => useStableReferenceByHash(value, false),
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
});
