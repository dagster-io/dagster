import React, {useMemo} from 'react';

// Alternates between 0 / 1, switching whenever the predicate evaluates to true.
export const usePredicateChangeSignal = <T extends ReadonlyArray<unknown>>(
  predicate: (previousDeps: T | null, currentDeps: T) => true | false | void,
  currentDeps: T,
) => {
  const previousDepsRef = React.useRef<T | null>(null);

  let didChange: void | boolean = false;
  useMemo(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
    didChange = predicate(previousDepsRef.current, currentDeps);
  }, currentDeps);

  const resultValueRef = React.useRef<1 | 0>(1);

  if (didChange) {
    previousDepsRef.current = currentDeps;
    resultValueRef.current = resultValueRef.current === 1 ? 0 : 1;
  }
  return resultValueRef.current;
};
