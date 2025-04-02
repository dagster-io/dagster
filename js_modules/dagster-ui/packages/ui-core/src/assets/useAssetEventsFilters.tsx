import {Box, Icon} from '@dagster-io/ui-components';
import React, {useCallback, useMemo} from 'react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {AssetKey} from './types';
import {featureEnabled} from '../app/Flags';
import {MaterializationHistoryEventTypeSelector} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {TruncatedTextWithFullTextOnHover} from '../nav/getLeftNavItemsForOption';
import {useFilters} from '../ui/BaseFilters';
import {usePartitionsForAssetKey} from './AutoMaterializePolicyPage/usePartitionsForAssetKey';
import {AssetViewDefinitionNodeFragment} from './types/AssetView.types';
import {useStaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';
import {useTimeRangeFilter} from '../ui/BaseFilters/useTimeRangeFilter';

type FilterState = {
  partitions?: string[];
  dateRange?: {
    start: number | null;
    end: number | null;
  };
  status?: string[];
  type?: string[];
};

type Config = {
  assetKey: AssetKey;
  assetNode: AssetViewDefinitionNodeFragment | null;
};

const emptyArray: string[] = [];

export const useAssetEventsFilters = ({assetKey, assetNode}: Config) => {
  const [filterState, _setFilterState] = useQueryPersistedState<FilterState>({
    queryKey: 'filters',
    behavior: 'push',
    decode: (raw) => {
      if (!raw?.partitions && !raw?.status && !raw?.type && !raw?.dateRange) {
        return {
          partitions: [],
          status: statusValues.map((s) => s.key),
          type: typeValues.map((t) => t.key),
        };
      }
      return {
        partitions: raw?.partitions,
        dateRange: raw?.dateRange
          ? {
              start: raw.dateRange.start ? parseInt(raw.dateRange.start) : null,
              end: raw.dateRange.end ? parseInt(raw.dateRange.end) : null,
            }
          : undefined,
        status: raw?.status,
        type: raw?.type,
      };
    },
    encode: (raw) => ({
      partitions: raw.partitions,
      dateRange: raw.dateRange,
      status: raw.status,
      type: raw.type,
    }),
  });

  const setFilterState = useCallback(
    (newFilterState: Partial<FilterState>) => {
      _setFilterState((prev) => ({...prev, ...newFilterState}));
    },
    [_setFilterState],
  );

  const {partitions} = usePartitionsForAssetKey(assetKey.path);

  const partitionValues = useMemo(
    () =>
      partitions.map((p) => ({
        key: p,
        value: p,
        match: [p],
      })),
    [partitions],
  );

  const partitionsFilter = useStaticSetFilter({
    name: 'Partitions',
    icon: 'partition',
    allValues: partitionValues,
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="job" />
        <TruncatedTextWithFullTextOnHover text={value} />
      </Box>
    ),
    getStringValue: (x) => x,
    state: React.useMemo(() => new Set(filterState.partitions), [filterState.partitions]),
    onStateChanged: (values) => {
      setFilterState({partitions: Array.from(values)});
    },
  });

  const statusFilter = useStaticSetFilter({
    name: 'Status',
    icon: 'status',
    allValues: statusValues,
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="job" />
        <TruncatedTextWithFullTextOnHover text={value} />
      </Box>
    ),
    getStringValue: (x) => {
      if (x === MaterializationHistoryEventTypeSelector.MATERIALIZATION) {
        return 'Success';
      } else if (x === MaterializationHistoryEventTypeSelector.FAILED_TO_MATERIALIZE) {
        return 'Failure';
      }
      return x;
    },
    state: React.useMemo(() => new Set(filterState.status ?? emptyArray), [filterState.status]),
    onStateChanged: (values) => {
      setFilterState({status: Array.from(values)});
    },
    showActiveState: (state) => state.size !== statusValues.length,
    canSelectAll: false,
  });

  const typeFilter = useStaticSetFilter({
    name: 'Type',
    icon: 'filter',
    allValues: typeValues,
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="job" />
        <TruncatedTextWithFullTextOnHover text={value} />
      </Box>
    ),
    getStringValue: (x) => x,
    state: React.useMemo(() => new Set(filterState.type ?? emptyArray), [filterState.type]),
    onStateChanged: (values) => {
      setFilterState({type: Array.from(values)});
    },
    showActiveState: (state) => state.size !== typeValues.length,
    canSelectAll: false,
  });

  const dateRangeFilter = useTimeRangeFilter({
    name: 'Date',
    icon: 'date',
    state: useMemo(() => {
      return filterState.dateRange
        ? [filterState.dateRange.start, filterState.dateRange.end]
        : undefined;
    }, [filterState.dateRange]),
    onStateChanged: (values) => {
      if (!values[0] && !values[1]) {
        setFilterState({dateRange: undefined});
      } else {
        setFilterState({
          dateRange: {
            start: values[0] ? new Date(values[0]).getTime() : null,
            end: values[1] ? new Date(values[1]).getTime() : null,
          },
        });
      }
    },
  });

  const filters = useMemo(() => {
    const filters = [];
    if (featureEnabled(FeatureFlag.flagUseNewObserveUIs)) {
      filters.push(statusFilter);
    }
    filters.push(dateRangeFilter);
    if (assetNode?.partitionDefinition) {
      filters.push(partitionsFilter);
    }
    if (!assetNode?.isMaterializable) {
      // No need to show the type filter for assets without materializations
      filters.push(typeFilter);
    }
    return filters;
  }, [
    statusFilter,
    dateRangeFilter,
    assetNode?.partitionDefinition,
    assetNode?.isMaterializable,
    partitionsFilter,
    typeFilter,
  ]);

  const {button: filterButton, activeFiltersJsx} = useFilters({filters});

  return {filterButton, activeFiltersJsx, filterState};
};

const statusValues = [
  {
    key: MaterializationHistoryEventTypeSelector.MATERIALIZATION,
    value: MaterializationHistoryEventTypeSelector.MATERIALIZATION,
    match: ['Success'],
  },
  {
    key: MaterializationHistoryEventTypeSelector.FAILED_TO_MATERIALIZE,
    value: MaterializationHistoryEventTypeSelector.FAILED_TO_MATERIALIZE,
    match: ['Failure'],
  },
];

const typeValues = [
  {key: 'Materialization', value: 'Materialization', match: ['Materialization']},
  {key: 'Observation', value: 'Observation', match: ['Observation']},
];
