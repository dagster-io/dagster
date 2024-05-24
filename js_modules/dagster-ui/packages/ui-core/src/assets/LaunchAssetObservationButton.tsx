import {ApolloClient, useApolloClient} from '@apollo/client';
import {Button, Icon, Spinner, Tooltip} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';

import {
  AssetsInScope,
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
import {CloudOSSContext} from '../app/CloudOSSContext';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {LaunchPipelineExecutionMutationVariables} from '../runs/types/RunUtils.types';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';

type ObserveAssetsState =
  | {type: 'none'}
  | {type: 'loading'}
  | {type: 'error'; error: string}
  | {
      type: 'single-run';
      executionParams: LaunchPipelineExecutionMutationVariables['executionParams'];
    };

export const useObserveAction = (preferredJobName?: string) => {
  const {useLaunchWithTelemetry} = useLaunchPadHooks();
  const launchWithTelemetry = useLaunchWithTelemetry();
  const client = useApolloClient();
  const [state, setState] = useState<ObserveAssetsState>({type: 'none'});

  const onClick = async (assetKeys: AssetKey[], e: React.MouseEvent<any>) => {
    if (state.type === 'loading') {
      return;
    }
    setState({type: 'loading'});

    const result = await client.query<LaunchAssetLoaderQuery, LaunchAssetLoaderQueryVariables>({
      query: LAUNCH_ASSET_LOADER_QUERY,
      variables: {assetKeys},
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

  return {onClick, loading: state.type === 'loading'};
};

export const LaunchAssetObservationButton = ({
  scope,
  preferredJobName,
  primary = false,
}: {
  scope: AssetsInScope;
  primary?: boolean;
  preferredJobName?: string;
}) => {
  const {onClick, loading} = useObserveAction(preferredJobName);
  const scopeAssets = 'selected' in scope ? scope.selected : scope.all;

  const {
    featureContext: {canSeeMaterializeAction},
  } = useContext(CloudOSSContext);

  if (!canSeeMaterializeAction) {
    return null;
  }

  if (!scopeAssets.length) {
    return <></>;
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
        <Button
          intent={primary ? 'primary' : undefined}
          icon={<Icon name="observation" />}
          disabled
        >
          {label}
        </Button>
      </Tooltip>
    );
  }

  return (
    <Button
      intent={primary ? 'primary' : undefined}
      onClick={(e) => onClick(scopeAssets.map(asAssetKeyInput), e)}
      icon={loading ? <Spinner purpose="body-text" /> : <Icon name="observation" />}
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
      error: 'One or more of the selected source assets is not an observable asset.',
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
