import {Body, Box, Colors, Spinner} from '@dagster-io/ui';
import * as React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {SidebarSection} from '../pipelines/SidebarComponents';

import {AssetEventSystemTags} from './AssetEventSystemTags';
import {AssetMaterializationGraphs} from './AssetMaterializationGraphs';
import {CurrentMinutesLateTag, freshnessPolicyDescription} from './CurrentMinutesLateTag';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunSinceMaterializationBanner} from './FailedRunSinceMaterializationBanner';
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
  } = useRecentAssetEvents(assetKey, {}, {assetHasDefinedPartitions});

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
      {!assetHasDefinedPartitions && (
        <>
          <FailedRunSinceMaterializationBanner
            run={liveData?.runWhichFailedToMaterialize || null}
            border={{side: 'top', width: 1, color: Colors.KeylineGray}}
          />
          <CurrentRunsBanner
            liveData={liveData}
            border={{side: 'top', width: 1, color: Colors.KeylineGray}}
          />
        </>
      )}

      {liveData?.freshnessPolicy && (
        <SidebarSection title="Freshness policy">
          <Box margin={{horizontal: 24, vertical: 12}} flex={{gap: 12, alignItems: 'center'}}>
            <CurrentMinutesLateTag liveData={liveData} />
            <Body>{freshnessPolicyDescription(liveData.freshnessPolicy)}</Body>
          </Box>
        </SidebarSection>
      )}

      <SidebarSection title="Materialization in last run">
        {materializations[0] ? (
          <div style={{margin: -1, maxWidth: '100%', overflowX: 'auto'}}>
            <LatestMaterializationMetadata
              assetKey={assetKey}
              latest={materializations[0]}
              liveData={liveData}
            />
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
      <SidebarSection title="Materialization system tags" collapsedByDefault>
        {materializations[0] ? (
          <div style={{margin: -1, maxWidth: '100%', overflowX: 'auto'}}>
            <AssetEventSystemTags event={materializations[0]} paddingLeft={24} />
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
      <SidebarSection title="Metadata plots">
        <AssetMaterializationGraphs
          xAxis={xAxis}
          asSidebarSection
          groups={grouped}
          columnCount={1}
        />
      </SidebarSection>
    </>
  );
};
