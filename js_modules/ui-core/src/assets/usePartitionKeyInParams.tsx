import {useCallback, useMemo} from 'react';

import {AssetViewParams} from './types';

export function usePartitionKeyInParams({
  params,
  setParams,
  dimensionCount,
  defaultKeyInDimension,
}: {
  params: AssetViewParams;
  setParams: (params: AssetViewParams) => void;
  dimensionCount: number;
  defaultKeyInDimension: (idx: number) => string | undefined;
}) {
  const focusedDimensionKeys = useMemo(
    () =>
      params.partition
        ? dimensionCount > 1
          ? params.partition.split('|').filter(Boolean) // 2D partition keys
          : [params.partition] // "|" character is allowed in 1D partition keys for historical reasons
        : [],
    [dimensionCount, params.partition],
  );

  const setFocusedDimensionKey = useCallback(
    (dimensionIdx: number, dimensionKey: string | undefined) => {
      // Automatically make a selection in column 0 if the user
      // clicked in column 1 and there is no column 0 selection.
      const nextFocusedDimensionKeys: string[] = [];
      for (let ii = 0; ii < dimensionIdx; ii++) {
        const val = focusedDimensionKeys[ii] || defaultKeyInDimension(ii);
        if (!val) {
          setParams({...params, partition: undefined});
          return;
        }
        nextFocusedDimensionKeys.push(val);
      }
      if (dimensionKey) {
        nextFocusedDimensionKeys.push(dimensionKey);
      }
      setParams({
        ...params,
        partition: nextFocusedDimensionKeys.join('|'),
      });
    },
    [defaultKeyInDimension, focusedDimensionKeys, params, setParams],
  );

  return [focusedDimensionKeys, setFocusedDimensionKey] as const;
}
