import React from 'react';

/**
 * Allows you to easily support updating state based on previous state.
 *
 * usage:
 * function useMyCustomStateHook() {
 *   const [state, setState] = useState(initialState);
 *   const update = (nextState: T) => {
 *     setState(doSomeFancyCalculation(nextState));
 *   };
 *   return [state, useSetStateUpdateCallback(state, update)];
 * }
 */
export function useSetStateUpdateCallback<T>(
  initialCurrentState: T,
  updateCallback: (next: T) => void,
): (next: React.SetStateAction<T>) => void {
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

  return update;
}
