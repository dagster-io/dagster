import {Button, Icon, Tooltip} from '@dagster-io/ui';
import React from 'react';

import {isSourceAsset} from '../asset-graph/Utils';
import {LaunchRootExecutionButton} from '../launchpad/LaunchRootExecutionButton';
import {DagsterTag} from '../runs/RunTag';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {LaunchAssetChoosePartitionsDialog} from './LaunchAssetChoosePartitionsDialog';
import {AssetKey} from './types';

type AssetMinimal = {
  assetKey: {path: string[]};
  opNames: string[];
  jobNames: string[];
  partitionDefinition: string | null;
  repository: {name: string; location: {name: string}};
};

export const LaunchAssetExecutionButton: React.FC<{
  preferredJobName?: string;
  assets: AssetMinimal[];
  upstreamAssetKeys: AssetKey[];
  title?: string;
}> = ({assets, preferredJobName, upstreamAssetKeys, title}) => {
  const [showingPartitionDialog, setShowingPartitionDialog] = React.useState(false);
  const repoAddress = buildRepoAddress(
    assets[0]?.repository.name || '',
    assets[0]?.repository.location.name || '',
  );

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

  title = title || 'Refresh';
  if (partitionDefinition) {
    // Add ellipsis to the button title since it will open a "Choose partitions" modal
    title =
      title.indexOf(' (') !== -1
        ? title.slice(0, title.indexOf(' (')) + '...' + title.slice(title.indexOf(' ('))
        : title + '...';
  }

  return (
    <Tooltip content={disabledReason}>
      {partitionDefinition ? (
        <>
          <Button
            icon={<Icon name="materialization" />}
            disabled={!!disabledReason}
            intent="primary"
            onClick={() => setShowingPartitionDialog(true)}
          >
            {title}
          </Button>
          <LaunchAssetChoosePartitionsDialog
            assets={assets}
            upstreamAssetKeys={upstreamAssetKeys}
            repoAddress={repoAddress}
            assetJobName={jobName}
            open={showingPartitionDialog}
            setOpen={setShowingPartitionDialog}
          />
        </>
      ) : (
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
      )}
    </Tooltip>
  );
};
