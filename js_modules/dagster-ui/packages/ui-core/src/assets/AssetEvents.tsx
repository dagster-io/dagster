import {
  Box,
  ButtonGroup,
  Colors,
  ErrorBoundary,
  NonIdealState,
  Spinner,
  Subheading,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {useMemo} from 'react';

import {AssetEventDetail, AssetEventDetailEmpty} from './AssetEventDetail';
import {AssetEventList} from './AssetEventList';
import {AssetPartitionDetail, AssetPartitionDetailEmpty} from './AssetPartitionDetail';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunSinceMaterializationBanner} from './FailedRunSinceMaterializationBanner';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {AssetEventGroup, useGroupedEvents} from './groupByPartition';
import {AssetKey, AssetViewParams} from './types';
import {AssetViewDefinitionNodeFragment} from './types/AssetView.types';
import {useAssetDefinition} from './useAssetDefinition';
import {useAssetEventsFilters} from './useAssetEventsFilters';
import {usePaginatedAssetEvents} from './usePaginatedAssetEvents';
import {getXAxisForParams} from './useRecentAssetEvents';
import {LiveDataForNode, stepKeyForAsset} from '../asset-graph/Utils';
import {MaterializationHistoryEventTypeSelector, RepositorySelector} from '../graphql/types';

interface Props {
  assetKey: AssetKey;
  assetNode: AssetViewDefinitionNodeFragment | null;
  liveData?: LiveDataForNode;
  params: AssetViewParams;
  paramsTimeWindowOnly: boolean;
  setParams: (params: AssetViewParams) => void;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  dataRefreshHint: string | undefined;

  repository?: RepositorySelector;
  opName?: string | null;
}

export const AssetEvents = ({
  assetKey,
  assetNode,
  params,
  setParams,
  liveData,
  dataRefreshHint,
}: Props) => {
  /**
   * We have a separate "Asset > Partitions" tab, but that is only available for SDAs with
   * pre-defined partitions. For non-SDAs, this Events page still displays a "Time | Partition"
   * picker and this xAxis can still be `partitions`!
   *
   * The partitions behavior in this case isn't ideal because the UI only "sees" partition names
   * in the events it has fetched. Users should upgrade to SDAs for a better experience.
   *
   * To test this easily, unload / break your code location so your SDA becomes a non-SDA :-)
   */
  const xAxis = getXAxisForParams(params, {defaultToPartitions: false});

  const {filterButton, activeFiltersJsx, filterState} = useAssetEventsFilters({
    assetKey,
    assetNode,
  });

  const combinedParams = useMemo(() => {
    const combinedParams: Parameters<typeof usePaginatedAssetEvents>[1] = {...params};
    if (filterState.dateRange) {
      if (filterState.dateRange.end) {
        combinedParams.before = filterState.dateRange.end;
      }
      if (filterState.dateRange.start) {
        combinedParams.after = filterState.dateRange.start;
      }
    }
    return combinedParams;
  }, [params, filterState.dateRange]);

  const {materializations, observations, loadedPartitionKeys, fetchMore, fetchLatest, loading} =
    usePaginatedAssetEvents(assetKey, combinedParams);

  React.useEffect(() => {
    fetchLatest();
  }, [
    params.asOf,
    dataRefreshHint,
    fetchLatest,
    combinedParams.after,
    combinedParams.before,
    combinedParams.status,
    combinedParams.partitions,
  ]);

  const grouped = useGroupedEvents(
    xAxis,
    filterState.type?.includes('Materialization') ? materializations : [],
    filterState.type?.includes('Observation') ? observations : [],
    loadedPartitionKeys,
  );

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
    !assetNode?.partitionDefinition && grouped.some((g) => g.partition);
  const assetHasLineage = materializations.some(
    (m) => 'assetLineage' in m && m.assetLineage.length > 0,
  );

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

  const {cachedDefinition, definition} = useAssetDefinition(assetKey);

  const def = definition ?? cachedDefinition;

  const hasFilter =
    combinedParams.status !== MaterializationHistoryEventTypeSelector.ALL ||
    combinedParams.before !== undefined ||
    combinedParams.after !== undefined ||
    combinedParams.partitions !== undefined;
  if (!loading && !materializations.length && !observations.length && !hasFilter) {
    return (
      <Box padding={{horizontal: 24, vertical: 64}}>
        <NonIdealState
          shrinkable
          icon="materialization_planned"
          title="This asset has not been materialized yet."
          description="An asset materialization is the process of executing the function associated with an asset definition. This typically writes data to persistent storage."
          action={
            def ? (
              <LaunchAssetExecutionButton
                scope={{all: [def]}}
                showChangedAndMissingOption={false}
              />
            ) : null
          }
        />
      </Box>
    );
  }

  return (
    <>
      <Box border="bottom" padding={{vertical: 16, horizontal: 24}}>
        {filterButton}
      </Box>
      {activeFiltersJsx.length ? (
        <Box
          border="bottom"
          padding={{vertical: 16, horizontal: 24}}
          flex={{direction: 'row', gap: 4, alignItems: 'center'}}
        >
          {activeFiltersJsx}
        </Box>
      ) : null}
      {assetHasUndefinedPartitions && (
        <Box
          flex={{justifyContent: 'space-between', alignItems: 'center'}}
          border="bottom"
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

      {assetNode && !assetNode.partitionDefinition && (
        <>
          <FailedRunSinceMaterializationBanner
            stepKey={stepKeyForAsset(assetNode)}
            border="bottom"
            run={liveData?.runWhichFailedToMaterialize || null}
          />
          <CurrentRunsBanner
            stepKey={stepKeyForAsset(assetNode)}
            border="bottom"
            liveData={liveData}
          />
        </>
      )}

      <Box
        style={{flex: 1, minHeight: 0, outline: 'none'}}
        flex={{direction: 'row'}}
        onKeyDown={onKeyDown}
        tabIndex={-1}
      >
        {(() => {
          if (!grouped.length && !loading) {
            return (
              <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{flex: 1}}>
                <NonIdealState
                  icon="materialization_planned"
                  title="No events found"
                  description="No events found for the selected filters."
                />
              </Box>
            );
          }
          return (
            <>
              <Box
                style={{display: 'flex', flex: 1, minWidth: 200}}
                flex={{direction: 'column'}}
                background={Colors.backgroundLight()}
              >
                {loading && grouped.length === 0 ? (
                  <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{flex: 1}}>
                    <Spinner purpose="section" />
                  </Box>
                ) : (
                  <AssetEventList
                    xAxis={xAxis}
                    groups={grouped}
                    focused={focused}
                    setFocused={onSetFocused}
                    loading={loading}
                    onLoadMore={fetchMore}
                  />
                )}
              </Box>

              <Box
                flex={{direction: 'column'}}
                style={{flex: 3, minWidth: 0, overflowY: 'auto'}}
                border="left"
              >
                <ErrorBoundary region="event" resetErrorOnChange={[focused]}>
                  {xAxis === 'partition' ? (
                    focused ? (
                      <AssetPartitionDetail
                        group={focused}
                        hasLineage={assetHasLineage}
                        assetKey={assetKey}
                        stepKey={assetNode ? stepKeyForAsset(assetNode) : undefined}
                        latestRunForPartition={null}
                        changedReasons={assetNode?.changedReasons}
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
            </>
          );
        })()}
      </Box>
    </>
  );
};
