import {AssetCheckHandleInput} from '../graphql/types';

import {LaunchAssetExecutionAssetNodeFragment} from './types/LaunchAssetExecutionButton.types';

export function getAssetCheckHandleInputs(
  assets: Pick<LaunchAssetExecutionAssetNodeFragment, 'assetKey' | 'assetChecksOrError'>[],
  jobName?: string,
): AssetCheckHandleInput[] {
  return assets.flatMap((a) =>
    a.assetChecksOrError.__typename === 'AssetChecks'
      ? a.assetChecksOrError.checks
          // For user code prior to 1.5.10 jobNames isn't populated, so don't filter on it
          .filter(
            (check) => !jobName || check.jobNames.length === 0 || check.jobNames.includes(jobName),
          )
          .map((check) => ({
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
