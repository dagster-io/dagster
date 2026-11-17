import {MiddleTruncate} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {assetDetailsPathForAssetCheck, assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetKey} from './types';
import {COMMON_COLLATOR} from '../app/Util';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {sortByValue} from '../util/sortByValue';

export type Check = {name: string; assetKey: AssetKey};

export const sortedAssetKeys = <T extends AssetKey>(keys: readonly T[]) =>
  sortByValue(keys, displayNameForAssetKey, COMMON_COLLATOR.compare);

export const sortedAssetChecks = <T extends Check>(checks: readonly T[]) =>
  sortByValue(checks, labelForAssetCheck, COMMON_COLLATOR.compare);

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
