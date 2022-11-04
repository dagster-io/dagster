import {Box, Button, Colors, Subheading} from '@dagster-io/ui';
import React from 'react';

import {useAssetGraphData} from '../asset-graph/useAssetGraphData';
import {LaunchAssetExecutionButton} from '../assets/LaunchAssetExecutionButton';
import {usePartitionHealthData} from '../assets/PartitionHealthSummary';
import {useViewport} from '../gantt/useViewport';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {JobBackfillsTable} from './JobBackfillsTable';
import {CountBox} from './OpJobPartitionsView';
import {PartitionState, PartitionStatus} from './PartitionStatus';
import {PartitionPerAssetStatus} from './PartitionStepStatus';

export const AssetJobPartitionsView: React.FC<{
  pipelineName: string;
  partitionSetName: string;
  repoAddress: RepoAddress;
}> = ({partitionSetName, repoAddress, pipelineName}) => {
  const {viewport, containerProps} = useViewport();
  const repositorySelector = repoAddressToSelector(repoAddress);

  const assetGraph = useAssetGraphData('', {
    pipelineSelector: {
      pipelineName,
      repositoryName: repoAddress.name,
      repositoryLocationName: repoAddress.location,
    },
  });

  const assetHealth = usePartitionHealthData(assetGraph.graphAssetKeys);
  const partitionNames = Array.from(new Set<string>(assetHealth.flatMap((a) => a.keys)));
  const jobHealth = React.useMemo(
    () =>
      Object.fromEntries(
        partitionNames.map((p) => [
          p,
          assetHealth.every((asset) =>
            p in asset.statusByPartition ? asset.statusByPartition[p] === true : true,
          )
            ? PartitionState.SUCCESS
            : PartitionState.MISSING,
        ]),
      ),
    [assetHealth, partitionNames],
  );

  const [pageSize, setPageSize] = React.useState(60);
  const [offset, setOffset] = React.useState<number>(0);
  const [showSteps, setShowSteps] = React.useState(false);

  React.useEffect(() => {
    if (viewport.width && !showSteps) {
      // magical numbers to approximate the size of the window, which is calculated in the step
      // status component.  This approximation is to make sure that the window does not jump as
      // the pageSize gets recalculated
      const _approximatePageSize = Math.ceil((viewport.width - 330) / 32) - 3;
      setPageSize(_approximatePageSize);
    }
  }, [viewport.width, showSteps, setPageSize]);

  const selectedPartitions = showSteps
    ? partitionNames.slice(
        Math.max(0, partitionNames.length - 1 - offset - pageSize),
        partitionNames.length - offset,
      )
    : partitionNames;

  return (
    <div>
      <Box
        flex={{justifyContent: 'space-between', direction: 'row', alignItems: 'center'}}
        border={{width: 1, side: 'bottom', color: Colors.KeylineGray}}
        padding={{vertical: 16, horizontal: 24}}
      >
        <Subheading>Status</Subheading>
        <Box flex={{gap: 8}}>
          <Button onClick={() => setShowSteps(!showSteps)}>
            {showSteps ? 'Hide per-asset status' : 'Show per-asset status'}
          </Button>
          <LaunchAssetExecutionButton
            context="all"
            assetKeys={assetGraph.graphAssetKeys}
            preferredJobName={pipelineName}
          />
        </Box>
      </Box>
      <Box
        flex={{direction: 'row', alignItems: 'center'}}
        border={{width: 1, side: 'bottom', color: Colors.KeylineGray}}
        padding={{left: 8}}
      >
        <CountBox count={partitionNames.length} label="Total partitions" />
        <CountBox
          count={partitionNames.filter((x) => jobHealth[x] === PartitionState.MISSING).length}
          label="Missing partitions"
        />
      </Box>
      <Box padding={{vertical: 16, horizontal: 24}}>
        <div {...containerProps}>
          <PartitionStatus
            partitionNames={partitionNames}
            partitionData={jobHealth}
            selected={showSteps ? selectedPartitions : undefined}
            selectionWindowSize={pageSize}
            onClick={(partitionName) => {
              const maxIdx = partitionNames.length - 1;
              const selectedIdx = partitionNames.indexOf(partitionName);
              const nextOffset = Math.min(
                maxIdx,
                Math.max(0, maxIdx - selectedIdx - 0.5 * pageSize),
              );
              setOffset(nextOffset);
              if (!showSteps) {
                setShowSteps(true);
              }
            }}
            tooltipMessage="Click to view per-step status"
          />
        </div>
        {showSteps && (
          <Box margin={{top: 16}}>
            <PartitionPerAssetStatus
              partitionNames={partitionNames}
              assetHealth={assetHealth}
              assetQueryItems={assetGraph.graphQueryItems}
              pipelineName={pipelineName}
              setPageSize={setPageSize}
              offset={offset}
              setOffset={setOffset}
            />
          </Box>
        )}
      </Box>
      <Box
        padding={{horizontal: 24, vertical: 16}}
        border={{side: 'horizontal', color: Colors.KeylineGray, width: 1}}
        style={{marginBottom: -1}}
      >
        <Subheading>Backfill history</Subheading>
      </Box>
      <Box margin={{bottom: 20}}>
        <JobBackfillsTable
          partitionSetName={partitionSetName}
          repositorySelector={repositorySelector}
          partitionNames={partitionNames}
          refetchCounter={1}
        />
      </Box>
    </div>
  );
};
