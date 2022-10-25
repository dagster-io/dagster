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
  } = useRecentAssetEvents(assetKey, assetHasDefinedPartitions, params);

  const grouped = useGroupedEvents(xAxis, materializations, observations, loadedPartitionKeys);
  const activeItems = React.useMemo(() => new Set([xAxis]), [xAxis]);

  if (loading) {
    return (
      <Box>
        <Box
          flex={{justifyContent: 'space-between', alignItems: 'center'}}
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
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
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
        style={{marginBottom: -1}}
      >
        <Subheading>Asset Plots</Subheading>

        {assetHasDefinedPartitions ? (
          <div style={{margin: '-6px 0 '}}>
            <ButtonGroup
              activeItems={activeItems}
              buttons={[
                {id: 'partition', label: 'By partition'},
                {id: 'time', label: 'By timestamp'},
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
