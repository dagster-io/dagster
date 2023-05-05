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
  currentState: T,
  updateCallback: (next: T) => void,
): (next: React.SetStateAction<T>) => void {
  const stateRef = React.useRef<T>(currentState);
  stateRef.current = currentState;

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
