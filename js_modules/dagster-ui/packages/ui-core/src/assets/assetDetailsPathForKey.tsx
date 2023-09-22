import qs from 'qs';

import {AssetKey, AssetViewParams} from './types';

export const assetDetailsPathForKey = (key: AssetKey, query?: AssetViewParams) => {
  return `/assets/${key.path.map(encodeURIComponent).join('/')}?${qs.stringify(query)}`;
};
