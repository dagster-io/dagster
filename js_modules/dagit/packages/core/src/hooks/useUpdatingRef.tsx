import React from 'react';

export const useUpdatingRef = <T,>(value: T): React.MutableRefObject<T> => {
  const ref = React.useRef(value);
  ref.current = value;
  return ref;
};
