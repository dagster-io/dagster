import {useEffect, useState} from 'react';

export const useDelayedState = (delayMsec: number) => {
  const [value, setValue] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setValue(true), delayMsec);
    return () => clearTimeout(timer);
  }, [delayMsec]);

  return value;
};
