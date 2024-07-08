import {createContext, useCallback, useContext, useEffect, useRef, useState} from 'react';
import {unstable_batchedUpdates} from 'react-dom';

import {useUpdatingRef} from './useUpdatingRef';

const MIN_DELAY_30FPS = 32;
const PREFERRED_DELAY_MULTIPLIER = 4;

/**
 * Context to accumulate updates over 200ms and batch them together to reduce the number of renders
 * Using a context instead of global state to make it easier to reset state across tests.
 */
export const ThrottledMemoBatchingContext = createContext<{enqueue: (update: () => void) => void}>(
  (() => {
    let isScheduled = false;
    const queue: Array<() => void> = [];
    return {
      enqueue: (update: () => void) => {
        queue.push(update);
        if (!isScheduled) {
          isScheduled = true;
          setTimeout(() => {
            unstable_batchedUpdates(() => {
              while (queue.length) {
                queue.shift()!();
              }
              isScheduled = false;
            });
          }, 200);
        }
      },
    };
  })(),
);

export const useThrottledMemo = <T,>(
  factoryArg: () => T,
  deps: React.DependencyList,
  throttleDelay?: number,
): T => {
  const throttleDelayRef = useUpdatingRef(throttleDelay);
  const delayRef = useRef(MIN_DELAY_30FPS); // 32ms = 30fps - Only used if throttleDelay is not passed in
  const factory = useCallback(() => {
    const start = Date.now();
    const res = factoryArg();
    const end = Date.now();

    // Multiply by 4 so that if this is slow to compute we don't use up all of the wall time.
    delayRef.current = Math.max((end - start) * PREFERRED_DELAY_MULTIPLIER, MIN_DELAY_30FPS);
    return res;
  }, [factoryArg]);

  const [state, setState] = useState<T>(factory);
  const lastRun = useRef<number>(Date.now());
  const timeoutId = useRef<NodeJS.Timeout | null>(null);
  const {enqueue} = useContext(ThrottledMemoBatchingContext);

  useEffect(() => {
    // If no delay is passed in then use the dynamic delay from delayRef
    const delay = throttleDelayRef.current ?? delayRef.current;

    let isCancelled = false;
    const now = Date.now();
    if (now - lastRun.current >= delay) {
      enqueue(() => {
        setState(factory);
      });
      lastRun.current = now;
    } else {
      if (timeoutId.current) {
        clearTimeout(timeoutId.current);
      }
      timeoutId.current = setTimeout(
        () => {
          enqueue(() => {
            if (isCancelled) {
              return;
            }
            setState(factory);
          });
          lastRun.current = Date.now();
        },
        delay - (now - lastRun.current),
      );
    }

    return () => {
      isCancelled = true;
      if (timeoutId.current) {
        clearTimeout(timeoutId.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
};
