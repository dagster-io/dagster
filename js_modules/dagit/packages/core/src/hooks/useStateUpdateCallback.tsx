import React from 'react';

/**
 * Easily support updating state based on previous state without the boilerplate
 */
export function useStateWithUpdateCallback<T>(
  initialCurrentState: T,
  updateCallback: (next: T) => void,
): [T, (next: React.SetStateAction<T>) => void] {
  const stateRef = React.useRef<T>(initialCurrentState);
  if (stateRef.current !== initialCurrentState) {
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
