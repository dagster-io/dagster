import * as React from 'react';

import {tokenForAssetKey} from '../asset-graph/Utils';

const useSanitizedAssetSearch = (searchValue: string) => {
  return React.useMemo(() => {
    return (searchValue || '')
      .replace(/(( ?> ?)|\.|\/)/g, '/')
      .toLowerCase()
      .trim();
  }, [searchValue]);
};

export const useAssetSearch = <A extends {key: {path: string[]}}>(
  searchValue: string,
  assets: A[],
): A[] => {
  const sanitizedSearch = useSanitizedAssetSearch(searchValue);
  return React.useMemo(() => {
    // If there is no search value, match everything.
    if (!sanitizedSearch) {
      return assets;
    }
    return assets.filter((a) => tokenForAssetKey(a.key).toLowerCase().includes(sanitizedSearch));
  }, [assets, sanitizedSearch]);
};

export const useAssetNodeSearch = <A extends {assetKey: {path: string[]}}>(
  searchValue: string,
  assetNodes: A[],
): A[] => {
  const sanitizedSearch = useSanitizedAssetSearch(searchValue);

  return React.useMemo(() => {
    // If there is no search value, match everything.
    if (!sanitizedSearch) {
      return assetNodes;
    }
    return assetNodes.filter((a) =>
      tokenForAssetKey(a.assetKey).toLowerCase().includes(sanitizedSearch),
    );
  }, [assetNodes, sanitizedSearch]);
};
