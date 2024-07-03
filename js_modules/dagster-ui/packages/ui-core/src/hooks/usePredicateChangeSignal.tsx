import React from 'react';

// Alternates between 0 / 1, switching whenever the predicate calls `signalChanged`.
export const usePredicateChangeSignal = <T extends ReadonlyArray<unknown>>(
  predicate: (previousDeps: T | null, currentDeps: T, signalChanged: () => void) => any,
  currentDeps: T,
) => {
  const previousDepsRef = React.useRef<T | null>(null);

  let didChange = false;
  const signalChanged = () => {
    didChange = true;
  };
  predicate(previousDepsRef.current, currentDeps, signalChanged);

  const resultValueRef = React.useRef<1 | 0>(1);

  if (didChange) {
    previousDepsRef.current = currentDeps;
    resultValueRef.current = resultValueRef.current === 1 ? 0 : 1;
  }
  return resultValueRef.current;
};
