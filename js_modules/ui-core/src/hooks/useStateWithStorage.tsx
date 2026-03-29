import * as React from 'react';

import {getJSONForKey} from '../util/getJSONForKey';

const DID_WRITE_LOCALSTORAGE = '';

// Sentinel distinguishing "no in-memory override, read from localStorage" (undefined)
// from "user explicitly cleared state but storage write failed" (CLEARED).
const CLEARED = Symbol('cleared');

export function useStateWithStorage<T>(key: string, validate: (json: any) => T) {
  const [version, setVersion] = React.useState(0);

  const validateRef = React.useRef(validate);
  validateRef.current = validate;

  const listener = React.useCallback(
    (event: Event) => {
      if (event instanceof CustomEvent && event.detail === key) {
        setVersion((v) => v + 1);
      }
    },
    [key],
  );

  React.useEffect(() => {
    document.addEventListener(DID_WRITE_LOCALSTORAGE, listener);
    return () => document.removeEventListener(DID_WRITE_LOCALSTORAGE, listener);
  }, [listener]);

  // Note: This hook doesn't keep the loaded data in state -- instead it uses a version bit and
  // a ref to load the value from localStorage when the `key` changes or when the `version` changes.
  // This allows us to immediately return the saved value for `key` in the same render.
  // When localStorage is unavailable (e.g. QuotaExceededError), inMemoryOverrideRef is used
  // as a fallback backing store; the value does not survive page reloads in that case.

  const inMemoryOverrideRef = React.useRef<T | typeof CLEARED | undefined>(undefined);

  // Reset in-memory override when the key changes (e.g. navigating between graphs).
  // This is in a useEffect rather than the render body to avoid mutating refs during render,
  // which is unsafe under React Concurrent Mode (renders can be invoked multiple times before commit).
  React.useEffect(() => {
    inMemoryOverrideRef.current = undefined;
  }, [key]);

  const state = React.useMemo(() => {
    const mem = inMemoryOverrideRef.current;
    if (mem !== undefined) {
      // CLEARED means the user explicitly cleared state but the storage write failed;
      // treat as empty rather than falling through to stale localStorage data.
      return mem === CLEARED ? validate(undefined) : (mem as T);
    }
    return validate(getJSONForKey(key));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [validate, key, version]);

  const setStateInner = React.useCallback(
    (next: T | undefined) => {
      try {
        if (next === undefined) {
          window.localStorage.removeItem(key);
        } else {
          window.localStorage.setItem(key, JSON.stringify(next));
        }
        inMemoryOverrideRef.current = undefined;
      } catch {
        // QuotaExceededError or other storage failures — continue with in-memory state.
        // Use CLEARED sentinel when next is undefined so the read path returns empty
        // rather than falling through to stale localStorage data.
        inMemoryOverrideRef.current = next === undefined ? CLEARED : next;
      }
      document.removeEventListener(DID_WRITE_LOCALSTORAGE, listener);
      document.dispatchEvent(new CustomEvent(DID_WRITE_LOCALSTORAGE, {detail: key}));
      document.addEventListener(DID_WRITE_LOCALSTORAGE, listener);

      setVersion((v) => v + 1);

      return next;
    },
    [key, listener],
  );

  const setState = React.useCallback(
    (input: React.SetStateAction<T>) => {
      const mem = inMemoryOverrideRef.current;
      // Exclude the CLEARED sentinel — treat it the same as undefined (read from storage).
      const current =
        mem !== undefined && mem !== CLEARED ? mem : validateRef.current(getJSONForKey(key));
      const next = input instanceof Function ? input(current) : input;
      setStateInner(next);
    },
    [key, setStateInner],
  );

  const clearState = React.useCallback(() => {
    setStateInner(undefined);
  }, [setStateInner]);

  return [state, setState, clearState] as const;
}
