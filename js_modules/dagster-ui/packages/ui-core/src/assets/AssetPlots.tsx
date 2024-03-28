import {Box, ButtonGroup, SpinnerWithText} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {AssetMaterializationGraphs} from './AssetMaterializationGraphs';
import {useGroupedEvents} from './groupByPartition';
import {AssetKey, AssetViewParams} from './types';
import {useRecentAssetEvents} from './useRecentAssetEvents';

interface Props {
  assetKey: AssetKey;
  params: AssetViewParams;
  assetHasDefinedPartitions: boolean;
  setParams: (params: AssetViewParams) => void;
}

export const AssetPlots = ({assetKey, assetHasDefinedPartitions, params, setParams}: Props) => {
  const {materializations, observations, loadedPartitionKeys, loading, xAxis} =
    useRecentAssetEvents(assetKey, params, {assetHasDefinedPartitions});

  const grouped = useGroupedEvents(xAxis, materializations, observations, loadedPartitionKeys);
  const activeItems = useMemo(() => new Set([xAxis]), [xAxis]);

  return (
    <>
      {assetHasDefinedPartitions ? (
        <Box
          flex={{justifyContent: 'space-between', alignItems: 'center'}}
          border="bottom"
          padding={{vertical: 16, left: 24, right: 12}}
          style={{marginBottom: -1}}
        >
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
        </Box>
      ) : null}
      {loading ? (
        <Box padding={{vertical: 48}} flex={{direction: 'row', justifyContent: 'center'}}>
          <SpinnerWithText label="Loading plots…" />
        </Box>
      ) : (
        <AssetMaterializationGraphs xAxis={xAxis} groups={grouped} />
      )}
    </>
  );
};
