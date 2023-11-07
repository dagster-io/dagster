import {AssetCheckHandleInput} from '../graphql/types';

import {LaunchAssetExecutionAssetNodeFragment} from './types/LaunchAssetExecutionButton.types';

export function getAssetCheckHandleInputs(
  assets: Pick<LaunchAssetExecutionAssetNodeFragment, 'assetKey' | 'assetChecksOrError'>[],
): AssetCheckHandleInput[] {
  return assets.flatMap((a) =>
    a.assetChecksOrError.__typename === 'AssetChecks'
      ? a.assetChecksOrError.checks.map((check) => ({
          name: check.name,
          assetKey: {path: a.assetKey.path},
        }))
      : [],
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
