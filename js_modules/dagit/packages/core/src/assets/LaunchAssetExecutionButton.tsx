import {ApolloClient, gql, useApolloClient} from '@apollo/client';
import {Button, Icon, Spinner, Tooltip} from '@dagster-io/ui';
import pick from 'lodash/pick';
import uniq from 'lodash/uniq';
import React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {usePermissions} from '../app/Permissions';
import {isSourceAsset} from '../asset-graph/Utils';
import {useLaunchWithTelemetry} from '../launchpad/LaunchRootExecutionButton';
import {AssetLaunchpad} from '../launchpad/LaunchpadRoot';
import {DagsterTag} from '../runs/RunTag';
import {LaunchPipelineExecutionVariables} from '../runs/types/LaunchPipelineExecution';
import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';

import {ASSET_NODE_CONFIG_FRAGMENT, configSchemaForAssetNode} from './AssetConfig';
import {LaunchAssetChoosePartitionsDialog} from './LaunchAssetChoosePartitionsDialog';
import {AssetKey} from './types';
import {LaunchAssetExecutionAssetNodeFragment} from './types/LaunchAssetExecutionAssetNodeFragment';
import {
  LaunchAssetLoaderQuery,
  LaunchAssetLoaderQueryVariables,
} from './types/LaunchAssetLoaderQuery';
import {
  LaunchAssetLoaderResourceQuery,
  LaunchAssetLoaderResourceQueryVariables,
} from './types/LaunchAssetLoaderResourceQuery';

type LaunchAssetsState =
  | {type: 'none'}
  | {type: 'loading'}
  | {type: 'error'; error: string}
  | {
      type: 'launchpad';
      jobName: string;
      sessionPresets: Partial<IExecutionSession>;
      repoAddress: RepoAddress;
    }
  | {
      type: 'partitions';
      jobName: string;
      assets: LaunchAssetExecutionAssetNodeFragment[];
      upstreamAssetKeys: AssetKey[];
      repoAddress: RepoAddress;
    }
  | {
      type: 'single-run';
      executionParams: LaunchPipelineExecutionVariables['executionParams'];
    };

export const LaunchAssetExecutionButton: React.FC<{
  assetKeys: AssetKey[]; // Memoization not required
  context?: 'all' | 'selected';
  intent?: 'primary' | 'none';
  preferredJobName?: string;
}> = ({assetKeys, preferredJobName, context, intent = 'primary'}) => {
  const {canLaunchPipelineExecution} = usePermissions();
  const launchWithTelemetry = useLaunchWithTelemetry();

  const [state, setState] = React.useState<LaunchAssetsState>({type: 'none'});
  const client = useApolloClient();

  const count = assetKeys.length > 1 ? ` (${assetKeys.length})` : '';
  const label = `Materialize${
    context === 'all' ? ` all${count}` : context === 'selected' ? ` selected${count}` : count
  }`;

  if (!assetKeys.length || !canLaunchPipelineExecution.enabled) {
    return (
      <Tooltip
        content={
          !canLaunchPipelineExecution.enabled
            ? 'You do not have permission to materialize assets'
            : 'Select one or more assets to materialize.'
        }
      >
        <Button intent={intent} icon={<Icon name="materialization" />} disabled>
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
      variables: {assetKeys: assetKeys.map(({path}) => ({path}))},
    });
    const assets = result.data.assetNodes;
    const forceLaunchpad = e.shiftKey;

    const next = await stateForLaunchingAssets(client, assets, forceLaunchpad, preferredJobName);

    if (next.type === 'error') {
      showCustomAlert({
        title: 'Unable to Materialize',
        body: next.error,
      });
      setState({type: 'none'});
    } else if (next.type === 'single-run') {
      await launchWithTelemetry({executionParams: next.executionParams}, 'toast');
      setState({type: 'none'});
    } else {
      setState(next);
    }
  };

  return (
    <>
      <Tooltip content="Shift+click to add configuration">
        <Button
          intent={intent}
          onClick={onClick}
          icon={
            state.type === 'loading' ? (
              <Spinner purpose="body-text" />
            ) : (
              <Icon name="materialization" />
            )
          }
        >
          {label}
        </Button>
      </Tooltip>
      {state.type === 'launchpad' && (
        <AssetLaunchpad
          assetJobName={state.jobName}
          repoAddress={state.repoAddress}
          sessionPresets={state.sessionPresets}
          open={true}
          setOpen={() => setState({type: 'none'})}
        />
      )}
      {state.type === 'partitions' && (
        <LaunchAssetChoosePartitionsDialog
          assets={state.assets}
          upstreamAssetKeys={state.upstreamAssetKeys}
          repoAddress={state.repoAddress}
          assetJobName={state.jobName}
          open={true}
          setOpen={() => setState({type: 'none'})}
        />
      )}
    </>
  );
};

async function stateForLaunchingAssets(
  client: ApolloClient<any>,
  assets: LaunchAssetExecutionAssetNodeFragment[],
  forceLaunchpad: boolean,
  preferredJobName?: string,
): Promise<LaunchAssetsState> {
  if (assets.some(isSourceAsset)) {
    return {
      type: 'error',
      error: 'One or more source assets are selected and cannot be materialized.',
    };
  }

  const repoAddress = buildRepoAddress(
    assets[0]?.repository.name || '',
    assets[0]?.repository.location.name || '',
  );

  if (
    !assets.every(
      (a) =>
        a.repository.name === repoAddress.name &&
        a.repository.location.name === repoAddress.location,
    )
  ) {
    return {
      type: 'error',
      error: 'Assets must be in the same repository to be materialized together.',
    };
  }

  const partitionDefinition = assets.find((a) => !!a.partitionDefinition)?.partitionDefinition;
  if (assets.some((a) => a.partitionDefinition && a.partitionDefinition !== partitionDefinition)) {
    return {
      type: 'error',
      error: 'Assets must share a partition definition to be materialized together.',
    };
  }

  const everyAssetHasJob = (jobName: string) => assets.every((a) => a.jobNames.includes(jobName));
  const jobsInCommon = assets[0] ? assets[0].jobNames.filter(everyAssetHasJob) : [];
  const jobName = jobsInCommon.find((name) => name === preferredJobName) || jobsInCommon[0];
  if (!jobName) {
    return {
      type: 'error',
      error: 'Assets must be in the same job to be materialized together.',
    };
  }

  const resourceResult = await client.query<
    LaunchAssetLoaderResourceQuery,
    LaunchAssetLoaderResourceQueryVariables
  >({
    query: LAUNCH_ASSET_LOADER_RESOURCE_QUERY,
    variables: {
      pipelineSelector: {
        pipelineName: jobName,
        repositoryName: assets[0].repository.name,
        repositoryLocationName: assets[0].repository.location.name,
      },
    },
  });
  const pipeline = resourceResult.data.pipelineOrError;
  if (pipeline.__typename !== 'Pipeline') {
    return {
      type: 'error',
      error: `Pipeline ${jobName} does not exist.`,
    };
  }
  const requiredResourceKeys = assets.flatMap((a) => a.requiredResources.map((r) => r.resourceKey));
  const resources = pipeline.modes[0].resources.filter((r) =>
    requiredResourceKeys.includes(r.name),
  );
  const anyResourcesHaveConfig = resources.some((r) => r.configField);
  const anyResourcesHaveRequiredConfig = resources.some((r) => r.configField?.isRequired);

  const anyAssetsHaveConfig = assets.some((a) => configSchemaForAssetNode(a));
  if ((anyAssetsHaveConfig || anyResourcesHaveRequiredConfig) && partitionDefinition) {
    return {
      type: 'error',
      error:
        'Cannot materialize assets using both partitions and asset or required resource config.',
    };
  }

  // Ok! Assertions met, how do we launch this run

  if (partitionDefinition) {
    const assetKeys = new Set(assets.map((a) => JSON.stringify(a.assetKey)));
    const upstreamAssetKeys = uniq(
      assets.flatMap((a) => a.dependencyKeys.map(({path}) => JSON.stringify({path}))),
    )
      .filter((key) => !assetKeys.has(key))
      .map((key) => JSON.parse(key));

    return {
      type: 'partitions',
      assets,
      jobName,
      repoAddress,
      upstreamAssetKeys,
    };
  }
  if (anyAssetsHaveConfig || anyResourcesHaveConfig || forceLaunchpad) {
    const assetOpNames = assets.flatMap((a) => a.opNames || []);
    return {
      type: 'launchpad',
      jobName,
      repoAddress,
      sessionPresets: {
        flattenGraphs: true,
        assetSelection: assets.map((a) => ({assetKey: a.assetKey, opNames: a.opNames})),
        solidSelectionQuery: assetOpNames.map((name) => `"${name}"`).join(', '),
      },
    };
  }
  return {
    type: 'single-run',
    executionParams: executionParamsForAssetJob(repoAddress, jobName, assets, []),
  };
}

export function executionParamsForAssetJob(
  repoAddress: RepoAddress,
  jobName: string,
  assets: {assetKey: AssetKey; opNames: string[]}[],
  tags: {key: string; value: string}[],
): LaunchPipelineExecutionVariables['executionParams'] {
  return {
    mode: 'default',
    executionMetadata: {
      tags: [
        ...tags.map((t) => pick(t, ['key', 'value'])),
        {
          key: DagsterTag.StepSelection,
          value: assets.flatMap((o) => o.opNames).join(','),
        },
      ],
    },
    runConfigData: '{}',
    selector: {
      repositoryLocationName: repoAddress.location,
      repositoryName: repoAddress.name,
      pipelineName: jobName,
      assetSelection: assets.map((asset) => ({
        path: asset.assetKey.path,
      })),
    },
  };
}

export const LAUNCH_ASSET_EXECUTION_ASSET_NODE_FRAGMENT = gql`
  fragment LaunchAssetExecutionAssetNodeFragment on AssetNode {
    id
    opNames
    jobNames
    graphName
    partitionDefinition
    assetKey {
      path
    }
    dependencyKeys {
      path
    }
    repository {
      id
      name
      location {
        id
        name
      }
    }
    requiredResources {
      resourceKey
    }
    ...AssetNodeConfigFragment
  }
  ${ASSET_NODE_CONFIG_FRAGMENT}
`;

const LAUNCH_ASSET_LOADER_QUERY = gql`
  query LaunchAssetLoaderQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      ...LaunchAssetExecutionAssetNodeFragment
    }
  }
  ${LAUNCH_ASSET_EXECUTION_ASSET_NODE_FRAGMENT}
`;

const LAUNCH_ASSET_LOADER_RESOURCE_QUERY = gql`
  query LaunchAssetLoaderResourceQuery($pipelineSelector: PipelineSelector!) {
    pipelineOrError(params: $pipelineSelector) {
      ... on Pipeline {
        id
        modes {
          id
          resources {
            name
            description
            configField {
              name
              isRequired
              configType {
                ...ConfigTypeSchemaFragment
                recursiveConfigTypes {
                  ...ConfigTypeSchemaFragment
                }
              }
            }
          }
        }
      }
    }
  }
  ${CONFIG_TYPE_SCHEMA_FRAGMENT}
`;
