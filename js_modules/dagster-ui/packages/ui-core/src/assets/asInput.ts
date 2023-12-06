import {
  AssetCheck,
  AssetCheckCanExecuteIndividually,
  AssetCheckHandleInput,
} from '../graphql/types';

import {LaunchAssetExecutionAssetNodeFragment} from './types/LaunchAssetExecutionButton.types';

export function inMaterializeFunctionOrInJob(
  check: Pick<AssetCheck, 'jobNames' | 'canExecuteIndividually'>,
  jobName?: string,
) {
  const inMaterialize =
    check.canExecuteIndividually === AssetCheckCanExecuteIndividually.REQUIRES_MATERIALIZATION;
  const inJob = !jobName || check.jobNames.includes(jobName);

  return inMaterialize || inJob;
}

export function getAssetCheckHandleInputs(
  assets: Pick<LaunchAssetExecutionAssetNodeFragment, 'assetKey' | 'assetChecksOrError'>[],
  jobName?: string,
): AssetCheckHandleInput[] {
  return assets.flatMap((a) =>
    a.assetChecksOrError.__typename === 'AssetChecks'
      ? a.assetChecksOrError.checks
          .filter((check) => inMaterializeFunctionOrInJob(check, jobName))
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
