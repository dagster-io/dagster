import {useRef} from 'react';

export function usePrevious<T>(value: T) {
  const ref = useRef<T | undefined>(undefined);
  const current = ref.current;
  ref.current = value;
  return current;
}
