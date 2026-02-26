import {Box, ErrorBoundary, NonIdealState, Spinner} from '@dagster-io/ui-components';
import * as React from 'react';
import {useMemo} from 'react';

import {AssetEventDetail, AssetEventDetailEmpty} from './AssetEventDetail';
import {AssetEventList} from './AssetEventList';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunSinceMaterializationBanner} from './FailedRunSinceMaterializationBanner';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {AssetEventGroup, useGroupedEvents} from './groupByPartition';
import {AssetKey, AssetViewParams} from './types';
import {AssetViewDefinitionNodeFragment} from './types/AssetView.types';
import {useAssetDefinition} from './useAssetDefinition';
import {useAssetEventsFilters} from './useAssetEventsFilters';
import {usePaginatedAssetEvents} from './usePaginatedAssetEvents';
import {LiveDataForNode, stepKeyForAsset} from '../asset-graph/Utils';
import {AssetEventHistoryEventTypeSelector, RepositorySelector} from '../graphql/types';

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
  const {filterButton, activeFiltersJsx, filterState} = useAssetEventsFilters({
    assetKey,
    assetNode,
  });

  const combinedParams = useMemo(() => {
    const combinedParams: Parameters<typeof usePaginatedAssetEvents>[1] = {
      asOf: params.asOf,
    };

    if (filterState.dateRange) {
      if (filterState.dateRange.end) {
        combinedParams.before = filterState.dateRange.end;
      }
      if (filterState.dateRange.start) {
        combinedParams.after = filterState.dateRange.start;
      }
    }
    if (filterState.partitions) {
      combinedParams.partitions = filterState.partitions;
    }
    if (filterState.status?.length === 1) {
      const status = filterState.status[0];
      const statusesForStatus =
        status === 'Success'
          ? [
              AssetEventHistoryEventTypeSelector.MATERIALIZATION,
              AssetEventHistoryEventTypeSelector.OBSERVATION,
            ]
          : [AssetEventHistoryEventTypeSelector.FAILED_TO_MATERIALIZE];

      combinedParams.statuses = combinedParams.statuses
        ? combinedParams.statuses.filter((c) => statusesForStatus.includes(c))
        : statusesForStatus;
    }

    if (filterState.type?.length === 1) {
      const type = filterState.type[0];
      const statusesForType =
        type === 'Materialization'
          ? [
              AssetEventHistoryEventTypeSelector.MATERIALIZATION,
              AssetEventHistoryEventTypeSelector.FAILED_TO_MATERIALIZE,
            ]
          : [AssetEventHistoryEventTypeSelector.OBSERVATION];

      combinedParams.statuses = combinedParams.statuses
        ? combinedParams.statuses.filter((c) => statusesForType.includes(c))
        : statusesForType;
    }
    return combinedParams;
  }, [
    params.asOf,
    filterState.dateRange,
    filterState.status,
    filterState.type,
    filterState.partitions,
  ]);

  const {events, fetchMore, fetchLatest, loading} = usePaginatedAssetEvents(
    assetKey,
    combinedParams,
  );

  React.useEffect(() => {
    fetchLatest();
  }, [
    params.asOf,
    dataRefreshHint,
    fetchLatest,
    combinedParams.after,
    combinedParams.before,
    combinedParams.statuses,
    combinedParams.partitions,
  ]);

  const grouped = useGroupedEvents('time', events, []);

  const onSetFocused = (group: AssetEventGroup | undefined) => {
    const updates: Partial<AssetViewParams> = {
      time: group?.timestamp !== params.time ? group?.timestamp || '' : '',
    };
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

  const hasFilter = Object.keys(combinedParams).length > 0;

  if (!loading && !events.length && !hasFilter) {
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
              <Box style={{display: 'flex', flex: 1, minWidth: 200}} flex={{direction: 'column'}}>
                {loading && grouped.length === 0 ? (
                  <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{flex: 1}}>
                    <Spinner purpose="section" />
                  </Box>
                ) : (
                  <AssetEventList
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
                  {focused?.latest ? (
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
