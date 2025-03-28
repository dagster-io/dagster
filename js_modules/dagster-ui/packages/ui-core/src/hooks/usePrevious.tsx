import {useEffect, useRef} from 'react';

export const usePrevious = <T,>(value: T): T | undefined => {
  const ref = useRef<T>();
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
};

export const usePreviousDistinctValue = <T,>(value: T): T | undefined => {
  const ref = useRef<T>();
  const prev = useRef<T>();

  useEffect(() => {
    if (ref.current !== value) {
      prev.current = ref.current;
      ref.current = value;
    }
  }, [value]);
  return prev.current;
};
