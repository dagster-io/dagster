import {Box, ButtonGroup, Colors, Spinner, Subheading, ErrorBoundary} from '@dagster-io/ui';
import * as React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {RepositorySelector} from '../graphql/types';

import {AssetEventDetail, AssetEventDetailEmpty} from './AssetEventDetail';
import {AssetEventList} from './AssetEventList';
import {AssetPartitionDetail, AssetPartitionDetailEmpty} from './AssetPartitionDetail';
import {AssetViewParams} from './AssetView';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunSinceMaterializationBanner} from './FailedRunSinceMaterializationBanner';
import {AssetEventGroup, useGroupedEvents} from './groupByPartition';
import {AssetKey} from './types';
import {useRecentAssetEvents} from './useRecentAssetEvents';

interface Props {
  assetKey: AssetKey;
  liveData?: LiveDataForNode;
  params: AssetViewParams;
  paramsTimeWindowOnly: boolean;
  setParams: (params: AssetViewParams) => void;
  assetHasDefinedPartitions: boolean;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  dataRefreshHint: string | undefined;

  repository?: RepositorySelector;
  opName?: string | null;
}

export const AssetEvents: React.FC<Props> = ({
  assetKey,
  assetHasDefinedPartitions,
  params,
  setParams,
  liveData,
  dataRefreshHint,
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
  }, [params.asOf, dataRefreshHint, refetch]);

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

  // Note: This page still has a LOT of logic for displaying events by partition but it's only enabled
  // in one case -- when the asset is an old-school, non-software-defined asset with partition keys
  // on it's materializations but no defined partition set.
  //
  const assetHasUndefinedPartitions =
    !assetHasDefinedPartitions && grouped.some((g) => g.partition);
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
      {assetHasUndefinedPartitions && (
        <Box
          flex={{justifyContent: 'space-between', alignItems: 'center'}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
          padding={{vertical: 16, horizontal: 24}}
          style={{marginBottom: -1}}
        >
          <Subheading>Asset Events</Subheading>
          <div style={{margin: '-6px 0 '}}>
            <ButtonGroup
              activeItems={new Set([xAxis])}
              buttons={[
                {id: 'partition', label: 'By partition'},
                {id: 'time', label: 'By timestamp'},
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
        </Box>
      )}

      {!assetHasDefinedPartitions && (
        <>
          <FailedRunSinceMaterializationBanner
            run={liveData?.runWhichFailedToMaterialize || null}
            border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
          />
          <CurrentRunsBanner
            liveData={liveData}
            border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
          />
        </>
      )}

      <Box
        style={{flex: 1, minHeight: 0, outline: 'none'}}
        flex={{direction: 'row'}}
        onKeyDown={onKeyDown}
        tabIndex={-1}
      >
        <Box
          style={{display: 'flex', flex: 1, minWidth: 200}}
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
          flex={{direction: 'column'}}
          style={{flex: 3, minWidth: 0, overflowY: 'auto'}}
          border={{side: 'left', color: Colors.KeylineGray, width: 1}}
        >
          <ErrorBoundary region="event" resetErrorOnChange={[focused]}>
            {xAxis === 'partition' ? (
              focused ? (
                <AssetPartitionDetail
                  group={focused}
                  hasLineage={assetHasLineage}
                  assetKey={assetKey}
                  latestRunForPartition={null}
                />
              ) : (
                <AssetPartitionDetailEmpty />
              )
            ) : focused?.latest ? (
              <AssetEventDetail assetKey={assetKey} event={focused.latest} />
            ) : (
              <AssetEventDetailEmpty />
            )}
          </ErrorBoundary>
        </Box>
      </Box>
    </>
  );
};
