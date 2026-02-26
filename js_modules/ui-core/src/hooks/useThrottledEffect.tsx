import {DependencyList, useEffect, useRef, useState} from 'react';

/**
 * A custom hook that throttles the execution of an effect.
 *
 * @param {Function} callback - The effect callback to be throttled (can return a cleanup function)
 * @param {Array} dependencies - Array of dependencies for the effect
 * @param {number} delay - The minimum time (in ms) between effect executions
 */
export const useThrottledEffect = (
  callback: () => void | (() => void),
  dependencies: DependencyList | undefined,
  delay: number,
) => {
  const lastRun = useRef(0);
  const [throttledDeps, setThrottledDeps] = useState(dependencies);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const cleanupFnRef = useRef<undefined | (() => void)>(undefined);

  // Clear any pending timeouts on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Check if dependencies changed
  useEffect(() => {
    const now = Date.now();
    const elapsed = now - lastRun.current;

    // If enough time has passed since last execution, run immediately
    if (elapsed >= delay) {
      lastRun.current = now;
      setThrottledDeps(dependencies);
    } else {
      // Otherwise, schedule to run after the delay has passed
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        lastRun.current = Date.now();
        setThrottledDeps(dependencies);
      }, delay - elapsed);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  // The actual effect that only runs when throttledDeps change
  useEffect(() => {
    // Run cleanup from previous effect if it exists
    if (typeof cleanupFnRef.current === 'function') {
      cleanupFnRef.current();
      cleanupFnRef.current = undefined;
    }

    // Run the effect and store any returned cleanup function
    const cleanup = callback();
    if (typeof cleanup === 'function') {
      cleanupFnRef.current = cleanup;
    }

    // Cleanup function for the useEffect
    return () => {
      if (typeof cleanupFnRef.current === 'function') {
        cleanupFnRef.current();
        cleanupFnRef.current = undefined;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, throttledDeps);
};
