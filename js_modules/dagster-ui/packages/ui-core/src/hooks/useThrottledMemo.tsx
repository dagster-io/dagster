import {createContext, useContext, useEffect, useRef, useState} from 'react';
import {unstable_batchedUpdates} from 'react-dom';

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
  factory: () => T,
  deps: React.DependencyList,
  delay: number,
): T => {
  const [state, setState] = useState<T>(factory);
  const lastRun = useRef<number>(Date.now());
  const timeoutId = useRef<NodeJS.Timeout | null>(null);
  const {enqueue} = useContext(ThrottledMemoBatchingContext);

  useEffect(() => {
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
