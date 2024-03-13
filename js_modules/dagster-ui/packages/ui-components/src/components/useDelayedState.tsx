import {useEffect, useState} from 'react';

export const useDelayedState = (delayMsec: number) => {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setReady(true), delayMsec);
    return () => clearTimeout(timer);
  }, [delayMsec]);

  return ready;
};
