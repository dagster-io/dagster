import isEqual from 'lodash/isEqual';
import {useEffect, useRef} from 'react';

type Difference<T> = {
  previous: T;
  current: T;
};

type Changes<T> = {
  index: number;
  previous: T;
  current: T;
  differences: Partial<Record<keyof T, Difference<any>>>;
};

const getDifferences = <T extends Record<any, any>>(
  obj1: T,
  obj2: T,
): Partial<Record<keyof T, Difference<any>>> => {
  const diffs: Partial<Record<keyof T, Difference<any>>> = {};
  Object.keys({...obj1, ...obj2}).forEach((key) => {
    if (!isEqual(obj1[key], obj2[key])) {
      diffs[key as keyof T] = {previous: obj1[key], current: obj2[key]};
    }
  });
  return diffs;
};

/**
 * Hook for debugging what is changing across renders to debug unnecessary renders and figure out
 *  what needs memoization
 */
export const useDebugChanged = <T,>(objects: T[]): void => {
  const previousObjectsRef = useRef<T[]>(objects);

  useEffect(() => {
    const previousObjects = previousObjectsRef.current;
    const changes: Changes<T>[] = [];

    objects.forEach((obj, index) => {
      if (!isEqual(obj, previousObjects[index])) {
        changes.push({
          index,
          previous: previousObjects[index]!,
          current: obj,
          differences: getDifferences(previousObjects[index]!, obj!),
        });
      }
    });

    if (changes.length > 0) {
      console.log('Changed objects:', changes);
    }

    previousObjectsRef.current = objects;
  }, [objects]);
};
