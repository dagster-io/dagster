import * as React from 'react';

export const useDelayedState = (delayMsec: number) => {
  const [value, setValue] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => setValue(true), delayMsec);
    return () => clearTimeout(timer);
  }, [delayMsec]);

  return value;
};
