import React from 'react';

/**
 * Have a custom setter while supporting updating state based on previous state for your callers.
 * Without the boilerplate!
 */
export function useStateWithUpdateCallback<T>(
  initialCurrentState: T,
  updateCallback: (next: T) => void,
): [T, (next: React.SetStateAction<T>) => void] {
  const stateRef = React.useRef<T>(initialCurrentState);
  const previousInitialCurrentState = React.useRef(initialCurrentState);
  if (previousInitialCurrentState.current !== initialCurrentState) {
    stateRef.current = initialCurrentState;
  }

  const updateCallbackRef = React.useRef(updateCallback);
  updateCallbackRef.current = updateCallback;
  const update = React.useCallback((next: React.SetStateAction<T>) => {
    if (next instanceof Function) {
      stateRef.current = next(stateRef.current);
    } else {
      stateRef.current = next;
    }
    updateCallbackRef.current(stateRef.current);
  }, []);
  return [stateRef.current, update];
}
