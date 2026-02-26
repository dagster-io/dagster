import {useDeferredValue, useEffect, useState} from 'react';

export const useDelayedState = (delayMsec: number) => {
  const [_ready, setReady] = useState(false);
  const ready = useDeferredValue(_ready);

  useEffect(() => {
    const timer = setTimeout(() => setReady(true), delayMsec);
    return () => clearTimeout(timer);
  }, [delayMsec]);

  return ready;
};
