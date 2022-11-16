import {Box, ButtonGroup, Colors, Spinner, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {AssetMaterializationGraphs} from './AssetMaterializationGraphs';
import {AssetViewParams} from './AssetView';
import {useGroupedEvents} from './groupByPartition';
import {AssetKey} from './types';
import {useRecentAssetEvents} from './useRecentAssetEvents';

interface Props {
  assetKey: AssetKey;
  params: AssetViewParams;
  assetHasDefinedPartitions: boolean;
  setParams: (params: AssetViewParams) => void;
}

export const AssetPlots: React.FC<Props> = ({
  assetKey,
  assetHasDefinedPartitions,
  params,
  setParams,
}) => {
  const {
    materializations,
    observations,
    loadedPartitionKeys,
    loading,
    xAxis,
  } = useRecentAssetEvents(assetKey, params, {assetHasDefinedPartitions});

  const grouped = useGroupedEvents(xAxis, materializations, observations, loadedPartitionKeys);
  const activeItems = React.useMemo(() => new Set([xAxis]), [xAxis]);

  if (loading) {
    return (
      <Box>
        <Box
          flex={{justifyContent: 'space-between', alignItems: 'center'}}
          border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
          padding={{vertical: 16, left: 24, right: 12}}
          style={{marginBottom: -1}}
        >
          <Subheading>Asset Plots</Subheading>
        </Box>
        <Box padding={{vertical: 48}}>
          <Spinner purpose="page" />
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
        border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
        padding={{vertical: 16, left: 24, right: 12}}
        style={{marginBottom: -1}}
      >
        <Subheading>Asset Plots</Subheading>

        {assetHasDefinedPartitions ? (
          <div style={{margin: '-6px 0 '}}>
            <ButtonGroup
              activeItems={activeItems}
              buttons={[
                {id: 'partition', label: 'Partitions', icon: 'partition'},
                {id: 'time', label: 'Events', icon: 'materialization'},
              ]}
              onClick={(id: string) =>
                setParams(
                  id === 'time'
                    ? {...params, partition: undefined, time: ''}
                    : {...params, partition: '', time: undefined},
                )
              }
            />
          </div>
        ) : null}
      </Box>
      <AssetMaterializationGraphs xAxis={xAxis} groups={grouped} />
    </Box>
  );
};
