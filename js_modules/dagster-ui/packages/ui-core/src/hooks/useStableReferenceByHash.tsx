import {useMemo} from 'react';

import {hashObject} from '../util/hashObject';

/*
 * This hook is used to create a stable reference to a value that is based on its hash.
 * It is useful to avoid unsubscribing/re-subscribing to the same keys in case the reference changes but the keys are the same.
 * It is also useful to avoid re-rendering the component when the value changes but the hash is the same.
 */

const referenceCache = new Map<string, any>();

export const useStableReferenceByHash = <T,>(
  value: T,
  storeInMap = false,
  hashFn = hashObject,
): T => {
  const hash = useMemo(() => hashFn(value), [value, hashFn]);
  return useMemo(() => {
    const cached = referenceCache.get(hash);
    if (cached) {
      return cached;
    }
    if (storeInMap) {
      referenceCache.set(hash, value);
    }
    return value;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hash]);
};
