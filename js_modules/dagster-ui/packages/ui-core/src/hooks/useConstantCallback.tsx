import {useCallback} from 'react';

import {useUpdatingRef} from './useUpdatingRef';

/**
 * Useful when you want to use a callback inside of a useEffect
 * but you don't want the callback changing to cause the useEffect to cleanup and rerun the effect.
 */
export function useConstantCallback<T extends (...args: any[]) => any>(callback: T): T {
  const callbackRef = useUpdatingRef(callback);
  return useCallback((...args: any[]) => callbackRef.current(...args), [callbackRef]) as T;
}
