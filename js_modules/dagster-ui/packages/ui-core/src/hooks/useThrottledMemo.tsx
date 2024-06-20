import {useEffect, useRef, useState} from 'react';
import {unstable_batchedUpdates as batchedUpdates} from 'react-dom';

export const useThrottledMemo = <T,>(
  factory: () => T,
  deps: React.DependencyList,
  delay: number,
): T => {
  const [state, setState] = useState<T>(factory);
  const lastRun = useRef<number>(Date.now());
  const timeoutId = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const now = Date.now();
    if (now - lastRun.current >= delay) {
      batchedUpdates(() => {
        setState(factory);
      });
      lastRun.current = now;
    } else {
      if (timeoutId.current) {
        clearTimeout(timeoutId.current);
      }
      timeoutId.current = setTimeout(
        () => {
          batchedUpdates(() => {
            setState(factory);
          });
          lastRun.current = Date.now();
        },
        delay - (now - lastRun.current),
      );
    }

    return () => {
      if (timeoutId.current) {
        clearTimeout(timeoutId.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
};
