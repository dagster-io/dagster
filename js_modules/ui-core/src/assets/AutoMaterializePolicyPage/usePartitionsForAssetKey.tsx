import {useMemo} from 'react';

import {FULL_PARTITIONS_QUERY} from './FullPartitionsQuery';
import {FullPartitionsQuery, FullPartitionsQueryVariables} from './types/FullPartitionsQuery.types';
import {useQuery} from '../../apollo-client';
import {DimensionPartitionKeys} from '../../graphql/types';

const emptyArray: DimensionPartitionKeys[] = [];

export const usePartitionsForAssetKey = (
  assetKeyPath: string[],
): {partitions: string[]; loading: boolean} => {
  const fullPartitionsQueryResult = useQuery<FullPartitionsQuery, FullPartitionsQueryVariables>(
    FULL_PARTITIONS_QUERY,
    {
      variables: {
        assetKey: {path: assetKeyPath},
      },
    },
  );

  const {data, loading} = fullPartitionsQueryResult;

  let partitionKeys: DimensionPartitionKeys[] = emptyArray;
  if (data?.assetNodeOrError.__typename === 'AssetNode') {
    partitionKeys = data.assetNodeOrError.partitionKeysByDimension;
  }

  const partitions = useMemo(() => flattenPartitionKeys(partitionKeys), [partitionKeys]);
  return {partitions, loading};
};

export const flattenPartitionKeys = (partitionKeys: DimensionPartitionKeys[]): string[] => {
  if (partitionKeys.length > 2) {
    throw new Error('Only 2 dimensions are supported');
  }

  const [firstKeys, secondKeys] = partitionKeys;

  if (!firstKeys) {
    return [];
  }

  if (!secondKeys) {
    return firstKeys.partitionKeys;
  }

  const firstKeyList = firstKeys.partitionKeys.length ? firstKeys.partitionKeys : [''];
  const secondKeyList = secondKeys.partitionKeys.length ? secondKeys.partitionKeys : [''];

  return firstKeyList.flatMap((key1) => secondKeyList.map((key2) => `${key1}|${key2}`));
};
