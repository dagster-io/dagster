import {gql, useQuery} from '@apollo/client';
import {Button, Icon, Spinner, Tooltip} from '@dagster-io/ui';
import uniq from 'lodash/uniq';
import React from 'react';

import {isSourceAsset, LiveData} from '../asset-graph/Utils';
import {LaunchRootExecutionButton} from '../launchpad/LaunchRootExecutionButton';
import {AssetLaunchpad} from '../launchpad/LaunchpadRoot';
import {DagsterTag} from '../runs/RunTag';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {ASSET_NODE_CONFIG_FRAGMENT, configSchemaForAssetNode} from './AssetConfig';
import {LaunchAssetChoosePartitionsDialog} from './LaunchAssetChoosePartitionsDialog';
import {AssetKey} from './types';
import {LaunchAssetExecutionAssetNodeFragment} from './types/LaunchAssetExecutionAssetNodeFragment';
import {
  LaunchAssetLoaderQuery,
  LaunchAssetLoaderQueryVariables,
} from './types/LaunchAssetLoaderQuery';

export const LazyLaunchAssetExecutionButton: React.FC<{
  assetKeys: AssetKey[];
  liveDataByNode: LiveData;
}> = ({assetKeys, liveDataByNode}) => {
  const queryResult = useQuery<LaunchAssetLoaderQuery, LaunchAssetLoaderQueryVariables>(
    LAUNCH_ASSET_LOADER_QUERY,
    {
      skip: assetKeys.length === 0,
      variables: {assetKeys: assetKeys.map(({path}) => ({path}))},
    },
  );

  if (!assetKeys.length) {
    return (
      <Button intent="primary" icon={<Icon name="materialization" />} disabled>
        Materialize
      </Button>
    );
  }
  if (!queryResult.data || queryResult.loading) {
    return (
      <Button intent="primary" icon={<Spinner purpose="body-text" />}>
        Materialize
      </Button>
    );
  }

  return (
    <LaunchAssetExecutionButton
      assets={queryResult.data.assetNodes}
      liveDataByNode={liveDataByNode}
    />
  );
};

export const LaunchAssetExecutionButton: React.FC<{
  assets: LaunchAssetExecutionAssetNodeFragment[];
  liveDataByNode: LiveData;
  preferredJobName?: string;
}> = ({assets, preferredJobName, liveDataByNode}) => {
  const [showingDialog, setShowingDialog] = React.useState(false);
  const repoAddress = buildRepoAddress(
    assets[0]?.repository.name || '',
    assets[0]?.repository.location.name || '',
  );

  const upstreamAssetKeys = React.useMemo(() => {
    const assetKeySet = new Set(assets.map((a) => JSON.stringify({path: a.assetKey})));
    return uniq(assets.flatMap((a) => a.dependencyKeys.map(({path}) => JSON.stringify({path}))))
      .filter((key) => !assetKeySet.has(key))
      .map((key) => JSON.parse(key));
  }, [assets]);

  let disabledReason = '';
  if (assets.some(isSourceAsset)) {
    disabledReason = 'One or more source assets are selected and cannot be materialized.';
  }
  if (
    !assets.every(
      (a) =>
        a.repository.name === repoAddress.name &&
        a.repository.location.name === repoAddress.location,
    )
  ) {
    disabledReason =
      disabledReason || 'Assets must be in the same repository to be materialized together.';
  }

  const partitionDefinition = assets.find((a) => !!a.partitionDefinition)?.partitionDefinition;
  if (assets.some((a) => a.partitionDefinition && a.partitionDefinition !== partitionDefinition)) {
    disabledReason =
      disabledReason || 'Assets must share a partition definition to be materialized together.';
  }

  const everyAssetHasJob = (jobName: string) => assets.every((a) => a.jobNames.includes(jobName));
  const jobsInCommon = assets[0] ? assets[0].jobNames.filter(everyAssetHasJob) : [];
  const jobName = jobsInCommon.find((name) => name === preferredJobName) || jobsInCommon[0];
  if (!jobName) {
    disabledReason =
      disabledReason || 'Assets must be in the same job to be materialized together.';
  }

  const anyAssetsHaveConfig = assets.some((a) => configSchemaForAssetNode(a));

  if (anyAssetsHaveConfig && partitionDefinition) {
    disabledReason =
      disabledReason || 'Cannot materialize assets using both asset config and partitions.';
  }

  let tooltipChildren: React.ReactNode;
  let title = titleForLaunch(assets, liveDataByNode);

  if (anyAssetsHaveConfig) {
    const assetOpNames = assets.flatMap((a) => a.opNames || []);
    const sessionPresets = {
      solidSelection: assetOpNames,
      solidSelectionQuery: assetOpNames.map((name) => `"${name}"`).join(' '),
    };
    tooltipChildren = (
      <>
        <Button
          icon={<Icon name="materialization" />}
          disabled={!!disabledReason}
          intent="primary"
          onClick={() => setShowingDialog(true)}
        >
          {title}
        </Button>
        <AssetLaunchpad
          assetJobName={jobName}
          repoAddress={repoAddress}
          sessionPresets={sessionPresets}
          open={showingDialog}
          setOpen={setShowingDialog}
        />
      </>
    );
  } else if (partitionDefinition) {
    // Add ellipsis to the button title since it will open a "Choose partitions" modal
    title =
      title.indexOf(' (') !== -1
        ? title.slice(0, title.indexOf(' (')) + '...' + title.slice(title.indexOf(' ('))
        : title + '...';
    tooltipChildren = (
      <>
        <Button
          icon={<Icon name="materialization" />}
          disabled={!!disabledReason}
          intent="primary"
          onClick={() => setShowingDialog(true)}
        >
          {title}
        </Button>
        <LaunchAssetChoosePartitionsDialog
          assets={assets}
          upstreamAssetKeys={upstreamAssetKeys}
          repoAddress={repoAddress}
          assetJobName={jobName}
          open={showingDialog}
          setOpen={setShowingDialog}
        />
      </>
    );
  } else {
    tooltipChildren = (
      <LaunchRootExecutionButton
        pipelineName={jobName}
        disabled={!!disabledReason}
        title={title}
        icon="materialization"
        behavior="toast"
        getVariables={() => ({
          executionParams: {
            mode: 'default',
            executionMetadata: {
              tags: [
                {
                  key: DagsterTag.StepSelection,
                  value: assets
                    .map((o) => o.opNames)
                    .flat()
                    .join(','),
                },
              ],
            },
            runConfigData: {},
            selector: {
              repositoryLocationName: repoAddress.location,
              repositoryName: repoAddress.name,
              pipelineName: jobName,
              assetSelection: assets.map((asset) => ({
                path: asset.assetKey.path,
              })),
            },
          },
        })}
      />
    );
  }
  return <Tooltip content={disabledReason}>{tooltipChildren}</Tooltip>;
};

const titleForLaunch = (
  nodes: LaunchAssetExecutionAssetNodeFragment[],
  liveDataByNode: LiveData,
) => {
  const isRematerializeForAll = (nodes.length
    ? nodes.map((n) => liveDataByNode[n.id])
    : Object.values(liveDataByNode)
  ).every((e) => !!e?.lastMaterialization);

  const count = nodes.length !== 1 ? ` (${nodes.length})` : '';

  return `${isRematerializeForAll ? 'Rematerialize' : 'Materialize'} ${
    nodes.length === 0 || nodes.length === Object.keys(liveDataByNode).length
      ? `All${count}`
      : `Selected${count}`
  }`;
};

export const LAUNCH_ASSET_EXECUTION_ASSET_NODE_FRAGMENT = gql`
  fragment LaunchAssetExecutionAssetNodeFragment on AssetNode {
    id
    opNames
    jobNames
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
