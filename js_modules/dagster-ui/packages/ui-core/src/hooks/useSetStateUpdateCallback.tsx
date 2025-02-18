import * as React from 'react';

/**
 * Wraps a state update callback to support React's standard setState behavior pattern.
 * Allows callers to use either a direct value or an updater function that receives the
 * previous state, even when the underlying update mechanism isn't a React useState setter.
 *
 * @param currentState - The current state value to track
 * @param updateCallback - External callback that will receive the updated state
 * @returns A stable setState-like dispatch function that can be passed to components
 *
 * @example
 * function useExternalState(currentValue: T, updateFn: (current: T) => void): React.Dispatch<React.SetStateAction<T>> {
 *   return useSetStateUpdateCallback(currentValue, updateFn);
 * }
 */
export function useSetStateUpdateCallback<T>(
  currentState: T,
  updateCallback: (current: T) => void,
): React.Dispatch<React.SetStateAction<T>> {
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

/**
 * Wraps a state update callback to support partial state updates with object merging.
 * Similar to useState's functional update form, but merges partial state objects
 * rather than replacing the entire state. Useful for managing complex state objects.
 *
 * @param currentState - The current state object to track
 * @param updateCallback - External callback that will receive the merged state
 * @returns A tuple containing [stateRef, updateFunction] for partial state updates
 *
 * @example
 * // In a custom hook for managing partial updates
 * function usePartialExternalState(currentValue: T, updateFn: (current: T) => void) {
 *   return usePartialSetStateUpdateCallback(currentValue, updateFn);
 * }
 */
export function usePartialSetStateUpdateCallback<T>(
  currentState: T,
  updateCallback: (current: T) => void,
) {
  const stateRef = React.useRef<T>(currentState);
  stateRef.current = currentState;

  const updateCallbackRef = React.useRef(updateCallback);
  updateCallbackRef.current = updateCallback;

  const update = React.useCallback((next: ((current: T) => Partial<T>) | Partial<T>) => {
    if (next instanceof Function) {
      stateRef.current = {
        ...stateRef.current,
        ...next(stateRef.current),
      };
    } else {
      stateRef.current = {
        ...stateRef.current,
        ...next,
      };
    }
    updateCallbackRef.current(stateRef.current);
  }, []);

  return [stateRef, update] as const;
}
