import {useState} from 'react';
import {useLaunchWithTelemetry} from 'shared/launchpad/useLaunchWithTelemetry.oss';

import {
  LAUNCH_ASSET_LOADER_QUERY,
  buildAssetCollisionsAlert,
  executionParamsForAssetJob,
  getCommonJob,
} from './LaunchAssetExecutionButton';
import {asAssetKeyInput} from './asInput';
import {AssetKey} from './types';
import {
  LaunchAssetExecutionAssetNodeFragment,
  LaunchAssetLoaderQuery,
  LaunchAssetLoaderQueryVariables,
} from './types/LaunchAssetExecutionButton.types';
import {useApolloClient} from '../apollo-client';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {LaunchPipelineExecutionMutationVariables} from '../runs/types/RunUtils.types';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';

export type ObserveAssetsState =
  | {type: 'none'}
  | {type: 'loading'}
  | {type: 'error'; error: string}
  | {
      type: 'single-run';
      executionParams: LaunchPipelineExecutionMutationVariables['executionParams'];
    };

export const useObserveAction = (preferredJobName?: string) => {
  const launchWithTelemetry = useLaunchWithTelemetry();
  const client = useApolloClient();
  const [state, setState] = useState<ObserveAssetsState>({type: 'none'});

  const onClick = async (assetKeys: AssetKey[], _: React.MouseEvent<any>) => {
    if (state.type === 'loading') {
      return;
    }
    setState({type: 'loading'});

    const result = await client.query<LaunchAssetLoaderQuery, LaunchAssetLoaderQueryVariables>({
      query: LAUNCH_ASSET_LOADER_QUERY,
      variables: {assetKeys: assetKeys.map(asAssetKeyInput)},
    });

    if (result.data.assetNodeDefinitionCollisions.length) {
      showCustomAlert(buildAssetCollisionsAlert(result.data));
      setState({type: 'none'});
      return;
    }

    const assets = result.data.assetNodes;

    const next = await stateForObservingAssets(assets, preferredJobName);

    if (next.type === 'error') {
      showCustomAlert({
        title: 'Unable to observe',
        body: next.error,
      });
      setState({type: 'none'});
      return;
    }

    if (next.type === 'single-run') {
      await launchWithTelemetry({executionParams: next.executionParams}, 'toast');
      setState({type: 'none'});
    } else {
      setState(next);
    }
  };

  return {onClick, loading: state.type === 'loading'};
};

async function stateForObservingAssets(
  assets: LaunchAssetExecutionAssetNodeFragment[],
  preferredJobName?: string,
): Promise<ObserveAssetsState> {
  if (assets.some((x) => !x.isObservable)) {
    return {
      type: 'error',
      error: 'One or more of the selected assets is not an observable asset.',
    };
  }
  const repoAddress = buildRepoAddress(
    assets[0]?.repository.name || '',
    assets[0]?.repository.location.name || '',
  );
  const repoName = repoAddressAsHumanString(repoAddress);

  if (
    !assets.every(
      (a) =>
        a.repository.name === repoAddress.name &&
        a.repository.location.name === repoAddress.location,
    )
  ) {
    return {
      type: 'error',
      error: `Assets must be in ${repoName} to be materialized together.`,
    };
  }

  const jobName = getCommonJob(assets, preferredJobName);
  if (!jobName) {
    return {
      type: 'error',
      error: 'Assets must be in the same job to be observed together.',
    };
  }

  return {
    type: 'single-run',
    executionParams: executionParamsForAssetJob(repoAddress, jobName, assets, []),
  };
}
