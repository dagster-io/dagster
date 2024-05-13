import {useMemo} from 'react';

import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';

const useSanitizedAssetSearch = (searchValue: string) => {
  return useMemo(() => {
    return (searchValue || '')
      .replace(/(( ?> ?)|\.|\/)/g, '/')
      .toLowerCase()
      .trim();
  }, [searchValue]);
};

export const useAssetSearch = <A extends {key: AssetKeyInput} | {assetKey: AssetKeyInput}>(
  searchValue: string,
  assets: A[],
): A[] => {
  const sanitizedSearch = useSanitizedAssetSearch(searchValue);

  return useMemo(() => {
    // If there is no search value, match everything.
    if (!sanitizedSearch) {
      return assets;
    }
    return assets.filter((a) =>
      tokenForAssetKey('assetKey' in a ? a.assetKey : a.key)
        .toLowerCase()
        .includes(sanitizedSearch),
    );
  }, [assets, sanitizedSearch]);
};
