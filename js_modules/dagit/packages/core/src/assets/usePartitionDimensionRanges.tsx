import React from 'react';

import {isTimeseriesPartition, placeholderDimensionRange} from './MultipartitioningSupport';
import {PartitionHealthData, PartitionHealthDimensionRange} from './usePartitionHealthData';

export const usePartitionDimensionRanges = (
  assetHealth: Pick<PartitionHealthData, 'dimensions'>,
  knownPartitionNames: string[] = [],
  defaultSelectionMode: 'view' | 'launch',
) => {
  const [ranges, setRanges] = React.useState<PartitionHealthDimensionRange[]>(
    knownPartitionNames.map(placeholderDimensionRange),
  );

  React.useEffect(() => {
    if (assetHealth) {
      setRanges(
        assetHealth.dimensions.map((dimension) => ({
          dimension,
          selected:
            defaultSelectionMode === 'view'
              ? dimension.partitionKeys
              : defaultSelectionMode === 'launch'
              ? isTimeseriesPartition(dimension.partitionKeys[0])
                ? dimension.partitionKeys.slice(-1)
                : dimension.partitionKeys
              : [],
        })),
      );
    }
  }, [assetHealth, defaultSelectionMode]);

  return [ranges, setRanges] as const;
};
