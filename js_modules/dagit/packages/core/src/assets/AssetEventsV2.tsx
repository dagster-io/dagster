import {Box, Colors, Spinner} from '@dagster-io/ui';
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

  repository?: RepositorySelector;
  opName?: string | null;
}

export const AssetEventsV2: React.FC<Props> = ({
  assetKey,
  assetLastMaterializedAt,
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
  } = useRecentAssetEvents(assetKey, params, {assetHasDefinedPartitions: false});

  React.useEffect(() => {
    if (params.asOf) {
      return;
    }
    refetch();
  }, [params.asOf, assetLastMaterializedAt, refetch]);

  const grouped = useGroupedEvents(xAxis, materializations, observations, loadedPartitionKeys);

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

  const onKeyDown = (e: React.KeyboardEvent<any>) => {
    const shift = {ArrowDown: 1, ArrowUp: -1}[e.key];
    if (!shift || !focused || e.isDefaultPrevented()) {
      return;
    }
    const next = grouped[grouped.indexOf(focused) + shift];
    if (next) {
      e.preventDefault();
      onSetFocused(next);
    }
  };

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
        style={{flex: 1, minHeight: 0, outline: 'none'}}
        flex={{direction: 'row'}}
        onKeyDown={onKeyDown}
        tabIndex={-1}
      >
        <Box
          style={{display: 'flex', flex: 1}}
          flex={{direction: 'column'}}
          background={Colors.Gray50}
        >
          {loading ? (
            <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{flex: 1}}>
              <Spinner purpose="section" />
            </Box>
          ) : (
            <AssetEventList
              xAxis={xAxis}
              groups={grouped}
              focused={focused}
              setFocused={onSetFocused}
            />
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
