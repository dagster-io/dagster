import {Box, Colors, Spinner} from '@dagster-io/ui';
import * as React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {SidebarSection} from '../pipelines/SidebarComponents';

import {AssetMaterializationGraphs} from './AssetMaterializationGraphs';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunsSinceMaterializationBanner} from './FailedRunsSinceMaterializationBanner';
import {LatestMaterializationMetadata} from './LastMaterializationMetadata';
import {useGroupedEvents} from './groupByPartition';
import {AssetKey} from './types';
import {useRecentAssetEvents} from './useRecentAssetEvents';

interface Props {
  assetKey: AssetKey;
  liveData?: LiveDataForNode;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  assetLastMaterializedAt: string | undefined;

  // This is passed in because we need to know whether to default to partition
  // grouping /before/ loading all the data.
  assetHasDefinedPartitions: boolean;
}

export const AssetSidebarActivitySummary: React.FC<Props> = ({
  assetKey,
  assetLastMaterializedAt,
  assetHasDefinedPartitions,
  liveData,
}) => {
  const {
    materializations,
    observations,
    loadedPartitionKeys,
    loading,
    refetch,
    xAxis,
  } = useRecentAssetEvents(assetKey, assetHasDefinedPartitions, {});

  const grouped = useGroupedEvents(xAxis, materializations, observations, loadedPartitionKeys);

  React.useEffect(() => {
    refetch();
  }, [assetLastMaterializedAt, refetch]);

  if (loading) {
    return (
      <Box padding={{vertical: 20}}>
        <Spinner purpose="section" />
      </Box>
    );
  }
  return (
    <>
      <FailedRunsSinceMaterializationBanner liveData={liveData} />
      <CurrentRunsBanner liveData={liveData} />
      <SidebarSection title="Materialization in Last Run">
        {materializations[0] ? (
          <div style={{margin: -1, maxWidth: '100%', overflowX: 'auto'}}>
            <LatestMaterializationMetadata latest={materializations[0]} />
          </div>
        ) : (
          <Box
            margin={{horizontal: 24, vertical: 12}}
            style={{color: Colors.Gray500, fontSize: '0.8rem'}}
          >
            No materializations found
          </Box>
        )}
      </SidebarSection>
      <SidebarSection title="Metadata Plots">
        <AssetMaterializationGraphs xAxis={xAxis} asSidebarSection groups={grouped} />
      </SidebarSection>
    </>
  );
};
