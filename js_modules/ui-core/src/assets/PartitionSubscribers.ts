import {useEffect, useRef} from 'react';

const subscriptions: Array<() => void> = [];

export function usePartitionDataSubscriber(onInvalidate: () => void) {
  // Use a ref so that if the callback changes we don't retrigger the useEffect below
  const onInvalidateRef = useRef(onInvalidate);
  onInvalidateRef.current = onInvalidate;

  useEffect(() => {
    const cb = () => onInvalidateRef.current();
    subscriptions.push(cb);
    return () => {
      const index = subscriptions.indexOf(cb);
      if (index !== -1) {
        subscriptions.splice(index, 1);
      }
    };
  }, []);
}

export function invalidatePartitions() {
  subscriptions.forEach((s) => s());
}
