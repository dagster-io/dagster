import React from 'react';

import {AssetViewParams} from './AssetView';

export function usePartitionKeyInParams({
  params,
  setParams,
  dimensionCount,
  defaultKeyInDimension,
}: {
  params: AssetViewParams;
  setParams: (params: AssetViewParams) => void;
  dimensionCount: number;
  defaultKeyInDimension: (idx: number) => string;
}) {
  const focusedDimensionKeys = React.useMemo(
    () =>
      params.partition
        ? dimensionCount > 1
          ? params.partition.split('|').filter(Boolean) // 2D partition keys
          : [params.partition] // "|" character is allowed in 1D partition keys for historical reasons
        : [],
    [dimensionCount, params.partition],
  );

  const setFocusedDimensionKey = (dimensionIdx: number, dimensionKey: string | undefined) => {
    // Automatically make a selection in column 0 if the user
    // clicked in column 1 and there is no column 0 selection.
    const nextFocusedDimensionKeys: string[] = [];
    for (let ii = 0; ii < dimensionIdx; ii++) {
      nextFocusedDimensionKeys.push(focusedDimensionKeys[ii] || defaultKeyInDimension(ii));
    }
    if (dimensionKey) {
      nextFocusedDimensionKeys.push(dimensionKey);
    }
    setParams({
      ...params,
      partition: nextFocusedDimensionKeys.join('|'),
    });
  };

  return [focusedDimensionKeys, setFocusedDimensionKey] as const;
}
