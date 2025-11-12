import qs from 'qs';

import {AssetKey, AssetViewParams} from './types';

export const assetDetailsPathForKey = (key: AssetKey, query?: AssetViewParams) => {
  if (!query) {
    return `/assets/${key.path.map(encodeURIComponent).join('/')}`;
  }
  // Ensure partition comes before default_range in the URL
  const queryString = qs.stringify(query, {
    sort: (a, b) => {
      // Ensure partition comes before default_range
      if (a === 'partition' && b === 'default_range') {
        return -1;
      }
      if (a === 'default_range' && b === 'partition') {
        return 1;
      }
      // Otherwise maintain alphabetical order for other params
      return a < b ? -1 : a > b ? 1 : 0;
    },
  });
  return `/assets/${key.path.map(encodeURIComponent).join('/')}?${queryString}`;
};

export const assetDetailsPathForAssetCheck = (check: {assetKey: AssetKey; name: string}) => {
  return assetDetailsPathForKey(check.assetKey, {view: 'checks', checkDetail: check.name});
};
