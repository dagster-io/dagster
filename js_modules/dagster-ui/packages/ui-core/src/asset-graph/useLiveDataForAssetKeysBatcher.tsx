import React from 'react';

import {AssetKeyInput} from '../graphql/types';

import {buildLiveData} from './Utils';
export const useLiveDataForAssetKeysBatcher = (assetKeys: AssetKeyInput[], batchSize = 10) => {
  const [_, forceRerender] = React.useReducer((s) => s + 1, 0);
  const currentBatchIndexRef = React.useRef(0);
  const currentBatchIndex = currentBatchIndexRef.current;

  function setBatchIndex(nextIndex: number) {
    currentBatchIndexRef.current = nextIndex;
    forceRerender();
  }

  const prevAssetKeys = React.useRef(assetKeys);
  if (prevAssetKeys.current !== assetKeys) {
    currentBatchIndexRef.current = 0;
    prevAssetKeys.current = assetKeys;
  }

  const numberOfBatches = React.useMemo(() => {
    // Try fetching 50 at a time
    return Math.ceil(assetKeys.length / batchSize);
  }, [assetKeys.length, batchSize]);

  const currentBatch = React.useMemo(() => {
    const startIndex = currentBatchIndex * batchSize;
    return assetKeys.slice(startIndex, startIndex + batchSize);
  }, [assetKeys, currentBatchIndex, batchSize]);

  const allLiveDataByNodeRef = React.useRef<ReturnType<typeof buildLiveData>>({});

  return {
    currentBatch,
    setBatchData: React.useCallback((liveDataByNode: typeof allLiveDataByNodeRef.current) => {
      allLiveDataByNodeRef.current = Object.assign(
        {},
        allLiveDataByNodeRef.current,
        liveDataByNode,
      );
      return allLiveDataByNodeRef.current;
    }, []),
    allLiveDataByNode: allLiveDataByNodeRef.current,
    nextBatch: React.useCallback(() => {
      setBatchIndex((currentBatchIndexRef.current + 1) % numberOfBatches);
    }, [numberOfBatches]),
    isLastBatch: numberOfBatches === currentBatchIndex + 1,
  };
};
