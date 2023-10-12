import {AssetCheckHandleInput} from '../graphql/types';

import {AssetKey} from './types';

export function getAssetCheckHandleInputs(
  assets: {assetKey: AssetKey; assetChecks: {name: string}[]}[],
): AssetCheckHandleInput[] {
  return assets.flatMap((a) =>
    a.assetChecks.map((check) => ({name: check.name, assetKey: {path: a.assetKey.path}})),
  );
}

// The `.map` calls below sanitize the __typename and other possible fields out of the
// assetSelection / assetCheckSelection because GraphQL is strict about extra values.

export function asAssetKeyInput(assetOrAssetKey: {assetKey: {path: string[]}} | {path: string[]}) {
  return 'path' in assetOrAssetKey
    ? {path: assetOrAssetKey.path}
    : {path: assetOrAssetKey.assetKey.path};
}

export function asAssetCheckHandleInput(check: {name: string; assetKey: {path: string[]}}) {
  return {name: check.name, assetKey: {path: check.assetKey.path}};
}
