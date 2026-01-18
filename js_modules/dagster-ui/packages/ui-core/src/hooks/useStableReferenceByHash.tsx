import {useMemo} from 'react';

import {hashObject} from '../util/hashObject';

/*
 * This hook is used to create a stable reference to a value that is based on its hash.
 * It is useful to avoid unsubscribing/re-subscribing to the same keys in case the reference changes but the keys are the same.
 * It is also useful to avoid re-rendering the component when the value changes but the hash is the same.
 */

export const useStableReferenceByHash = <T,>(value: T, hashFn = hashObject): T => {
  const hash = useMemo(() => hashFn(value), [value, hashFn]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  return useMemo(() => value, [hash]);
};
