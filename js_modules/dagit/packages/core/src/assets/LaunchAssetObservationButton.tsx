import {ApolloClient, useApolloClient} from '@apollo/client';
import {Button, Spinner, Tooltip, Icon} from '@dagster-io/ui';
import React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {LaunchPipelineExecutionMutationVariables} from '../runs/types/RunUtils.types';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';

import {
  AssetsInScope,
  buildAssetCollisionsAlert,
  executionParamsForAssetJob,
  getCommonJob,
  LAUNCH_ASSET_LOADER_QUERY,
} from './LaunchAssetExecutionButton';
import {
  LaunchAssetExecutionAssetNodeFragment,
  LaunchAssetLoaderQuery,
  LaunchAssetLoaderQueryVariables,
} from './types/LaunchAssetExecutionButton.types';

type ObserveAssetsState =
  | {type: 'none'}
  | {type: 'loading'}
  | {type: 'error'; error: string}
  | {
      type: 'single-run';
      executionParams: LaunchPipelineExecutionMutationVariables['executionParams'];
    };

export const LaunchAssetObservationButton: React.FC<{
  scope: AssetsInScope;
  intent?: 'primary' | 'none';
  preferredJobName?: string;
}> = ({scope, preferredJobName, intent = 'none'}) => {
  const {useLaunchWithTelemetry} = useLaunchPadHooks();
  const launchWithTelemetry = useLaunchWithTelemetry();

  const [state, setState] = React.useState<ObserveAssetsState>({type: 'none'});
  const client = useApolloClient();

  const scopeAssets = 'selected' in scope ? scope.selected : scope.all;
  if (!scopeAssets.length) {
    return <span />;
  }

  const count = scopeAssets.length > 1 ? ` (${scopeAssets.length})` : '';
  const label =
    'selected' in scope
      ? `Observe selected${count}`
      : scope.skipAllTerm
      ? `Observe${count}`
      : `Observe sources ${count}`;

  const hasMaterializePermission = scopeAssets.every((a) => a.hasMaterializePermission);
  if (!hasMaterializePermission) {
    return (
      <Tooltip content="You do not have permission to observe source assets">
        <Button intent={intent} icon={<Icon name="observation" />} disabled>
          {label}
        </Button>
      </Tooltip>
    );
  }

  const onClick = async (e: React.MouseEvent<any>) => {
    if (state.type === 'loading') {
      return;
    }
    setState({type: 'loading'});

    const result = await client.query<LaunchAssetLoaderQuery, LaunchAssetLoaderQueryVariables>({
      query: LAUNCH_ASSET_LOADER_QUERY,
      variables: {assetKeys: scopeAssets.map((a) => ({path: a.assetKey.path}))},
    });

    if (result.data.assetNodeDefinitionCollisions.length) {
      showCustomAlert(buildAssetCollisionsAlert(result.data));
      setState({type: 'none'});
      return;
    }

    const assets = result.data.assetNodes;
    const forceLaunchpad = e.shiftKey;

    const next = await stateForObservingAssets(client, assets, forceLaunchpad, preferredJobName);

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

  return (
    <Button
      intent={intent}
      onClick={onClick}
      icon={
        state.type === 'loading' ? <Spinner purpose="body-text" /> : <Icon name="observation" />
      }
    >
      {label}
    </Button>
  );
};

async function stateForObservingAssets(
  _client: ApolloClient<any>,
  assets: LaunchAssetExecutionAssetNodeFragment[],
  _forceLaunchpad: boolean,
  preferredJobName?: string,
): Promise<ObserveAssetsState> {
  if (assets.some((x) => !x.isSource)) {
    return {
      type: 'error',
      error: 'One or more non-source assets are selected and cannot be observed.',
    };
  }

  if (assets.some((x) => !x.isObservable)) {
    return {
      type: 'error',
      error: 'One or more of the selected source assets are unversioned and cannot be observed.',
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
