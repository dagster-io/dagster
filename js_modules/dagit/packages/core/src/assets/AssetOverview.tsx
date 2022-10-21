import {Box, ButtonGroup, Colors, Spinner, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {RepositorySelector} from '../types/globalTypes';

import {AssetEventDetail, AssetEventDetailEmpty} from './AssetEventDetail';
import {AssetEventList} from './AssetEventList';
import {AssetPartitionDetail, AssetPartitionDetailEmpty} from './AssetPartitionDetail';
import {AssetViewParams} from './AssetView';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunsSinceMaterializationBanner} from './FailedRunsSinceMaterializationBanner';
import {AssetEventGroup, useGroupedEvents} from './groupByPartition';
import {AssetKey} from './types';
import {useRecentAssetEvents} from './useRecentAssetEvents';

interface Props {
  assetKey: AssetKey;
  liveData?: LiveDataForNode;
  params: AssetViewParams;
  paramsTimeWindowOnly: boolean;
  setParams: (params: AssetViewParams) => void;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  assetLastMaterializedAt: string | undefined;

  // This is passed in because we need to know whether to default to partition
  // grouping /before/ loading all the data.
  assetHasDefinedPartitions: boolean;
  repository?: RepositorySelector;
  opName?: string | null;
}

export const AssetOverview: React.FC<Props> = ({
  assetKey,
  assetLastMaterializedAt,
  assetHasDefinedPartitions,
  params,
  setParams,
  liveData,
}) => {
  const {
    xAxis,
    materializations,
    observations,
    loadedPartitionKeys,
    refetch,
    loading,
  } = useRecentAssetEvents(assetKey, assetHasDefinedPartitions, params);

  React.useEffect(() => {
    if (params.asOf) {
      return;
    }
    refetch();
  }, [params.asOf, assetLastMaterializedAt, refetch]);

  const grouped = useGroupedEvents(xAxis, materializations, observations, loadedPartitionKeys);
  const activeItems = React.useMemo(() => new Set([xAxis]), [xAxis]);

  const onSetFocused = (group: AssetEventGroup | undefined) => {
    const updates: Partial<AssetViewParams> =
      xAxis === 'time'
        ? {time: group?.timestamp !== params.time ? group?.timestamp || '' : ''}
        : {partition: group?.partition !== params.partition ? group?.partition || '' : ''};
    setParams({...params, ...updates});
  };

  const focused: AssetEventGroup | undefined =
    grouped.find((b) =>
      params.time
        ? Number(b.timestamp) <= Number(params.time)
        : params.partition
        ? b.partition === params.partition
        : false,
    ) || grouped[0];

  const assetHasLineage = materializations.some((m) => m.assetLineage.length > 0);

  return (
    <>
      <FailedRunsSinceMaterializationBanner
        liveData={liveData}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      />

      <CurrentRunsBanner
        liveData={liveData}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      />

      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
        border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
        padding={{vertical: 16, left: 24, right: 12}}
        style={{marginBottom: -1}}
      >
        <Subheading>Activity</Subheading>
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
                    ? {...params, partition: undefined, time: focused?.timestamp || ''}
                    : {...params, partition: focused?.partition || '', time: undefined},
                )
              }
            />
          </div>
        ) : null}
      </Box>

      <Box style={{flex: 1, minHeight: 0}} flex={{direction: 'row'}}>
        <Box style={{display: 'flex', flex: 1}} flex={{direction: 'column'}}>
          {loading ? (
            <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{flex: 1}}>
              <Spinner purpose="section" />
            </Box>
          ) : (
            <AssetEventList
              xAxis={xAxis}
              hasPartitions={assetHasDefinedPartitions}
              hasLineage={assetHasLineage}
              groups={grouped}
              focused={focused}
              setFocused={onSetFocused}
            />
          )}

          {loadedPartitionKeys && (
            <Box
              style={{color: Colors.Gray400}}
              padding={{vertical: 16, horizontal: 24}}
              border={{side: 'top', width: 1, color: Colors.KeylineGray}}
            >
              Showing materializations for the last {loadedPartitionKeys.length} partitions.
            </Box>
          )}
        </Box>

        <Box
          style={{flex: 3}}
          flex={{direction: 'column'}}
          border={{side: 'left', color: Colors.KeylineGray, width: 1}}
        >
          {xAxis === 'partition' ? (
            focused ? (
              <AssetPartitionDetail group={focused} hasLineage={assetHasLineage} />
            ) : (
              <AssetPartitionDetailEmpty />
            )
          ) : focused?.latest ? (
            <AssetEventDetail event={focused.latest} />
          ) : (
            <AssetEventDetailEmpty />
          )}
        </Box>
      </Box>
    </>
  );
};
