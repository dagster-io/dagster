import qs from 'qs';

import {AssetViewParams} from './AssetView';
import {AssetKey} from './types';

export const assetDetailsPathForKey = (key: AssetKey, query?: AssetViewParams) => {
  return `/assets/${key.path.map(encodeURIComponent).join('/')}?${qs.stringify(query)}`;
};
