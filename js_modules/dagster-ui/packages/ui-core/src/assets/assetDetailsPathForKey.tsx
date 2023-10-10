import qs from 'qs';

import {AssetKey, AssetViewParams} from './types';

export const assetDetailsPathForKey = (key: AssetKey, query?: AssetViewParams) => {
  return `/assets/${key.path.map(encodeURIComponent).join('/')}?${qs.stringify(query)}`;
};

export const assetDetailsPathForAssetCheck = (check: {assetKey: AssetKey; name: string}) => {
  return assetDetailsPathForKey(check.assetKey, {view: 'checks', checkDetail: check.name});
};
