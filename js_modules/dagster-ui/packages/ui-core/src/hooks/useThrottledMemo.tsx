import {useEffect, useRef, useState} from 'react';

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
      setState(factory);
      lastRun.current = now;
    } else {
      if (timeoutId.current) {
        clearTimeout(timeoutId.current);
      }
      timeoutId.current = setTimeout(
        () => {
          setState(factory);
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
