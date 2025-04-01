import {MiddleTruncate} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {assetDetailsPathForAssetCheck, assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetKey} from './types';
import {COMMON_COLLATOR} from '../app/Util';
import {displayNameForAssetKey} from '../asset-graph/Utils';

type Check = {name: string; assetKey: AssetKey};

export const sortItemAssetKey = (a: AssetKey, b: AssetKey) => {
  return COMMON_COLLATOR.compare(displayNameForAssetKey(a), displayNameForAssetKey(b));
};

export const sortItemAssetCheck = (a: Check, b: Check) => {
  return COMMON_COLLATOR.compare(labelForAssetCheck(a), labelForAssetCheck(b));
};

export const renderItemAssetKey = (assetKey: AssetKey) => (
  <Link to={assetDetailsPathForKey(assetKey)} style={{display: 'block', width: '100%'}}>
    <MiddleTruncate text={displayNameForAssetKey(assetKey)} />
  </Link>
);

export const renderItemAssetCheck = (assetCheck: Check) => (
  <Link to={assetDetailsPathForAssetCheck(assetCheck)} style={{display: 'block', width: '100%'}}>
    <MiddleTruncate text={labelForAssetCheck(assetCheck)} />
  </Link>
);

export const labelForAssetCheck = (check: Check) => {
  return `${check.name} on ${displayNameForAssetKey(check.assetKey)}`;
};
