import React from 'react';

import {placeholderDimensionRange} from './MultipartitioningSupport';
import {PartitionHealthData, PartitionHealthDimensionRange} from './usePartitionHealthData';

export const usePartitionDimensionRanges = (
  assetHealth: Pick<PartitionHealthData, 'dimensions'>,
  knownPartitionNames: string[] = [],
) => {
  const [ranges, setRanges] = React.useState<PartitionHealthDimensionRange[]>(
    knownPartitionNames.map(placeholderDimensionRange),
  );

  React.useEffect(() => {
    if (assetHealth) {
      setRanges(
        assetHealth.dimensions.map((dimension) => ({
          dimension,
          selected: dimension.partitionKeys,
        })),
      );
    }
  }, [assetHealth]);

  return [ranges, setRanges] as const;
};
