import {Box, Button, Colors, Subheading} from '@dagster-io/ui';
import React from 'react';

import {useAssetGraphData} from '../asset-graph/useAssetGraphData';
import {LaunchAssetExecutionButton} from '../assets/LaunchAssetExecutionButton';
import {mergedAssetHealth, explodePartitionKeysInRanges} from '../assets/MultipartitioningSupport';
import {usePartitionHealthData} from '../assets/usePartitionHealthData';
import {useViewport} from '../gantt/useViewport';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {JobBackfillsTable} from './JobBackfillsTable';
import {CountBox} from './OpJobPartitionsView';
import {PartitionState, PartitionStatus} from './PartitionStatus';
import {getVisibleItemCount, PartitionPerAssetStatus} from './PartitionStepStatus';
import {GRID_FLOATING_CONTAINER_WIDTH} from './RunMatrixUtils';

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
  const partitionNames = Array.from(
    new Set<string>(assetHealth.flatMap((a) => a.dimensions[0].partitionKeys)),
  );

  // TODO BG: This page will break if the job has assets with different partition sets

  const {total, missing, merged} = React.useMemo(() => {
    const merged = mergedAssetHealth(assetHealth);
    const ranges = merged.dimensions.map((d) => ({selected: d.partitionKeys, dimension: d}));
    const allKeys = explodePartitionKeysInRanges(ranges, merged.stateForKey);

    return {
      merged,
      total: allKeys.length,
      missing: allKeys.filter((p) => p.state === PartitionState.MISSING).length,
    };
  }, [assetHealth]);

  const [pageSize, setPageSize] = React.useState(60);
  const [offset, setOffset] = React.useState<number>(0);
  const [showAssets, setShowAssets] = React.useState(false);

  React.useEffect(() => {
    if (viewport.width && !showAssets) {
      // magical numbers to approximate the size of the window, which is calculated in the step
      // status component.  This approximation is to make sure that the window does not jump as
      // the pageSize gets recalculated
      const approxPageSize = getVisibleItemCount(viewport.width - GRID_FLOATING_CONTAINER_WIDTH);
      setPageSize(approxPageSize);
    }
  }, [viewport.width, showAssets, setPageSize]);

  const selectedPartitions = showAssets
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
          <Button onClick={() => setShowAssets(!showAssets)}>
            {showAssets ? 'Hide per-asset status' : 'Show per-asset status'}
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
        <CountBox count={total} label="Total partitions" />
        <CountBox count={missing} label="Missing partitions" />
      </Box>
      <Box padding={{vertical: 16, horizontal: 24}}>
        <div {...containerProps}>
          <PartitionStatus
            partitionNames={partitionNames}
            partitionStateForKey={(key) => merged.stateForSingleDimension(0, key)}
            selected={showAssets ? selectedPartitions : undefined}
            selectionWindowSize={pageSize}
            onClick={(partitionName) => {
              const maxIdx = partitionNames.length - 1;
              const selectedIdx = partitionNames.indexOf(partitionName);
              const nextOffset = Math.min(
                maxIdx,
                Math.max(0, maxIdx - selectedIdx - 0.5 * pageSize),
              );
              setOffset(nextOffset);
              if (!showAssets) {
                setShowAssets(true);
              }
            }}
            tooltipMessage="Click to view per-asset status"
          />
        </div>
        {showAssets && (
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
