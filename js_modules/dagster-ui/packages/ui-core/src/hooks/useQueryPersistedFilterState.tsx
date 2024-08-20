import {SetStateAction, useMemo} from 'react';

import {useQueryPersistedState} from './useQueryPersistedState';

type SetterType<T extends Record<string, any>, K extends keyof T & string> = {
  [P in K as `set${Capitalize<P>}`]: (value: SetStateAction<T[P]>) => void;
};

export const useQueryPersistedFilterState = <T extends Record<string, any | undefined>>(
  filterFields: readonly (keyof T)[],
): {
  state: T;
  setState: React.Dispatch<React.SetStateAction<T>>;
  setters: SetterType<T, Extract<keyof T, string>>;
} => {
  const encode = (filters: T) => {
    return filterFields.reduce((acc, field) => {
      const value = filters[field];
      acc[field] = value?.length
        ? (JSON.stringify(value) as T[keyof T])
        : (undefined as T[keyof T]);
      return acc;
    }, {} as T);
  };

  const decode = (qs: Record<string, string | undefined>) => {
    return filterFields.reduce((acc, field) => {
      acc[field] = qs[field as string] ? JSON.parse(qs[field]!) : [];
      return acc;
    }, {} as T);
  };

  const [state, setState] = useQueryPersistedState<T>({
    encode,
    decode,
  });

  const createSetters = () => {
    const setters = {} as SetterType<T, Extract<keyof T, string>>;

    filterFields.forEach((field) => {
      const fieldAsString = field as keyof T & string;
      const key = `set${
        fieldAsString.charAt(0).toUpperCase() + fieldAsString.slice(1)
      }` as keyof SetterType<T, Extract<keyof T, string>>;

      setters[key] = ((value: any) => {
        setState((prevState: T) => ({
          ...prevState,
          [fieldAsString]: value instanceof Function ? value(prevState[fieldAsString]) : value,
        }));
      }) as any;
    });

    return setters;
  };

  const setters = useMemo(createSetters, [filterFields, setState]);

  return {
    state,
    setState,
    setters,
  };
};
