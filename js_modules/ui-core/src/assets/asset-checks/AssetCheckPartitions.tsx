import {Box, Colors, NonIdealState, TextInput} from '@dagster-io/ui-components';
import {useCallback, useMemo, useState} from 'react';

import {AssetCheckPartitionDetail} from './AssetCheckPartitionDetail';
import {
  AssetCheckPartitionStatus,
  assetCheckPartitionStatusToText,
  assetCheckPartitionStatusesToStyle,
} from './AssetCheckPartitionStatus';
import {AssetCheckPartitionData, useAssetCheckPartitionData} from './useAssetCheckPartitionData';
import {PartitionDefinitionType} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {DimensionRangeWizard} from '../../partitions/DimensionRangeWizard';
import {assembleIntoSpans} from '../../partitions/SpanRepresentation';
import {testId} from '../../testing/testId';
import {AssetPartitionStatus} from '../AssetPartitionStatus';
import {PartitionListSelector} from '../PartitionListSelector';
import {PartitionStatusCheckboxes} from '../PartitionStatusCheckboxes';
import {getDefaultPartitionSort, sortPartitionKeys} from '../partitionSortUtils';
import {AssetKey} from '../types';
import {Range} from '../usePartitionHealthData';

interface AssetCheckPartitionsProps {
  assetKey: AssetKey;
  checkName: string;
}

const DISPLAYED_STATUSES: AssetCheckPartitionStatus[] = [
  AssetCheckPartitionStatus.MISSING,
  AssetCheckPartitionStatus.SKIPPED,
  AssetCheckPartitionStatus.IN_PROGRESS,
  AssetCheckPartitionStatus.SUCCEEDED,
  AssetCheckPartitionStatus.FAILED,
  AssetCheckPartitionStatus.EXECUTION_FAILED,
].sort();

const STATUS_ORDER: AssetCheckPartitionStatus[] = [
  AssetCheckPartitionStatus.MISSING,
  AssetCheckPartitionStatus.FAILED,
  AssetCheckPartitionStatus.EXECUTION_FAILED,
  AssetCheckPartitionStatus.SKIPPED,
  AssetCheckPartitionStatus.IN_PROGRESS,
  AssetCheckPartitionStatus.SUCCEEDED,
];

/** Map check partition statuses to asset partition statuses for the status bar display */
function checkStatusToAssetStatus(status: AssetCheckPartitionStatus): AssetPartitionStatus {
  switch (status) {
    case AssetCheckPartitionStatus.SUCCEEDED:
      return AssetPartitionStatus.MATERIALIZED;
    case AssetCheckPartitionStatus.FAILED:
    case AssetCheckPartitionStatus.EXECUTION_FAILED:
    case AssetCheckPartitionStatus.SKIPPED:
      return AssetPartitionStatus.FAILED;
    case AssetCheckPartitionStatus.IN_PROGRESS:
      return AssetPartitionStatus.MATERIALIZING;
    case AssetCheckPartitionStatus.MISSING:
      return AssetPartitionStatus.MISSING;
  }
}

/** Build Range[] (asset health format) from check data for a given dimension */
function buildHealthRangesForDim(partitionData: AssetCheckPartitionData, dimIdx: number): Range[] {
  const dim = partitionData.dimensions[dimIdx];
  if (!dim) {
    return [];
  }
  const keys = dim.partitionKeys;

  // Get serialized status set for each key, then assemble into spans
  const statusesCache = new Map<string, AssetPartitionStatus[]>();
  const spans = assembleIntoSpans(keys, (key) => {
    const checkStatuses = partitionData.statusesForDimAggregate(dimIdx, key);
    const assetStatuses = [...new Set(checkStatuses.map(checkStatusToAssetStatus))].sort();
    const serialized = assetStatuses.join(',');
    statusesCache.set(serialized, assetStatuses);
    return serialized;
  });

  return spans
    .map((span) => {
      const startKey = keys[span.startIdx];
      const endKey = keys[span.endIdx];
      if (!startKey || !endKey) {
        return null;
      }
      return {
        start: {key: startKey, idx: span.startIdx},
        end: {key: endKey, idx: span.endIdx},
        value: statusesCache.get(span.status) ?? [AssetPartitionStatus.MISSING],
      };
    })
    .filter((r): r is Range => r !== null);
}

export const AssetCheckPartitions = ({assetKey, checkName}: AssetCheckPartitionsProps) => {
  const {data: partitionData, loading} = useAssetCheckPartitionData(assetKey, checkName);

  const isMultiPartition = (partitionData?.dimensions.length ?? 0) > 1;

  if (loading) {
    return (
      <Box padding={32}>
        <NonIdealState title="Loading partitions..." icon="hourglass" />
      </Box>
    );
  }

  if (!partitionData || partitionData.partitions.length === 0) {
    return (
      <Box padding={32}>
        <NonIdealState
          title="No partition data available"
          description="This asset check does not have partition information or no partitions exist."
          icon="partition"
        />
      </Box>
    );
  }

  if (isMultiPartition) {
    return (
      <AssetCheckMultiPartitions
        assetKey={assetKey}
        checkName={checkName}
        partitionData={partitionData}
      />
    );
  }

  return (
    <AssetCheckSinglePartitions
      assetKey={assetKey}
      checkName={checkName}
      partitionData={partitionData}
    />
  );
};

// Single-dimension partition view (original behavior)
const AssetCheckSinglePartitions = ({
  assetKey,
  checkName,
  partitionData,
}: {
  assetKey: AssetKey;
  checkName: string;
  partitionData: AssetCheckPartitionData;
}) => {
  const [focusedPartitionKey, setFocusedPartitionKey] = useState<string | undefined>();
  const [searchValue, setSearchValue] = useState('');

  // Selection for the DimensionRangeWizard (matching asset behavior)
  const [selectedKeys, setSelectedKeys] = useState<string[]>(() => partitionData.partitions);

  const [statusFilters, setStatusFilters] = useQueryPersistedState<AssetCheckPartitionStatus[]>({
    defaults: {status: [...DISPLAYED_STATUSES].sort().join(',')},
    encode: (val) => ({status: [...val].sort().join(',')}),
    decode: (qs) => {
      const status = qs.status;
      if (typeof status === 'string') {
        return status
          .split(',')
          .filter((s): s is AssetCheckPartitionStatus =>
            DISPLAYED_STATUSES.includes(s as AssetCheckPartitionStatus),
          );
      }
      return [...DISPLAYED_STATUSES];
    },
  });

  const healthRanges = useMemo(() => buildHealthRangesForDim(partitionData, 0), [partitionData]);

  const {filteredPartitions, countsByStatus} = useMemo(() => {
    const counts: {[key: string]: number} = {
      [AssetCheckPartitionStatus.MISSING]: 0,
      [AssetCheckPartitionStatus.SKIPPED]: 0,
      [AssetCheckPartitionStatus.SUCCEEDED]: 0,
      [AssetCheckPartitionStatus.IN_PROGRESS]: 0,
      [AssetCheckPartitionStatus.FAILED]: 0,
      [AssetCheckPartitionStatus.EXECUTION_FAILED]: 0,
    };

    const selectedSet = new Set(selectedKeys);
    const allPartitions = partitionData.partitions;
    const filtered = allPartitions.filter((partition) => {
      if (!selectedSet.has(partition)) {
        return false;
      }

      if (searchValue && !partition.toLowerCase().includes(searchValue.toLowerCase())) {
        return false;
      }

      const primaryStatus = partitionData.statusForPartition(partition);

      counts[primaryStatus] = !counts[primaryStatus] ? 1 : counts[primaryStatus] + 1;
      return statusFilters.includes(primaryStatus);
    });

    return {filteredPartitions: filtered, countsByStatus: counts};
  }, [partitionData, statusFilters, searchValue, selectedKeys]);

  const sortedAndFilteredPartitions = useMemo(() => {
    if (partitionData.dimensions.length === 0) {
      return filteredPartitions;
    }

    const firstDimension = partitionData.dimensions[0];
    if (!firstDimension) {
      return filteredPartitions;
    }

    const dimensionType = firstDimension.type;
    const sortType = getDefaultPartitionSort(dimensionType as PartitionDefinitionType);
    return sortPartitionKeys(filteredPartitions, sortType);
  }, [filteredPartitions, partitionData]);

  const statusForPartition = (dimensionKey: string): AssetCheckPartitionStatus[] => {
    return [partitionData.statusForPartition(dimensionKey)];
  };

  const firstDimension = partitionData.dimensions[0];

  return (
    <>
      {firstDimension && (
        <Box padding={{vertical: 16, horizontal: 24}} border="bottom">
          <DimensionRangeWizard
            dimensionType={firstDimension.type as PartitionDefinitionType}
            partitionKeys={firstDimension.partitionKeys}
            health={{ranges: healthRanges}}
            selected={selectedKeys}
            setSelected={setSelectedKeys}
            showQuickSelectOptionsForStatuses={false}
          />
        </Box>
      )}
      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        border="bottom"
      >
        <div data-testid={testId('partitions-selected')}>
          {sortedAndFilteredPartitions.length.toLocaleString()} Partitions Selected
        </div>
        <PartitionStatusCheckboxes
          counts={countsByStatus}
          allowed={DISPLAYED_STATUSES}
          value={statusFilters}
          onChange={setStatusFilters}
          statusToText={assetCheckPartitionStatusToText}
        />
      </Box>

      <Box style={{flex: 1, minHeight: 0, outline: 'none'}} flex={{direction: 'row'}} tabIndex={-1}>
        <Box
          style={{display: 'flex', flex: 1, paddingRight: 1, minWidth: 200}}
          flex={{direction: 'column'}}
          border="right"
          background={Colors.backgroundLight()}
        >
          <Box
            border="bottom"
            background={Colors.backgroundDefault()}
            padding={{horizontal: 16, vertical: 8}}
          >
            <TextInput
              icon="search"
              fill
              style={{width: '100%'}}
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder="Filter by partition…"
            />
          </Box>

          <PartitionListSelector
            partitions={sortedAndFilteredPartitions}
            statusForPartition={statusForPartition}
            focusedDimensionKey={focusedPartitionKey}
            setFocusedDimensionKey={setFocusedPartitionKey}
            statusesToStyle={assetCheckPartitionStatusesToStyle}
            statusOrder={STATUS_ORDER}
          />
        </Box>

        <Box style={{flex: 3, minWidth: 0, overflowY: 'auto'}} flex={{direction: 'column'}}>
          {focusedPartitionKey ? (
            <AssetCheckPartitionDetail
              assetKey={assetKey}
              checkName={checkName}
              partitionKey={focusedPartitionKey}
            />
          ) : (
            <Box
              flex={{direction: 'column', justifyContent: 'center', alignItems: 'center'}}
              style={{height: '100%'}}
            >
              <Box style={{color: Colors.textLight()}}>Select a partition to view details</Box>
            </Box>
          )}
        </Box>
      </Box>
    </>
  );
};

// Multi-dimension partition view (two columns)
const AssetCheckMultiPartitions = ({
  assetKey,
  checkName,
  partitionData,
}: {
  assetKey: AssetKey;
  checkName: string;
  partitionData: AssetCheckPartitionData;
}) => {
  // Find the time dimension index (prefer it as the primary/status-bar dimension)
  const timeDimensionIdx = partitionData.dimensions.findIndex(
    (d) => d.type === PartitionDefinitionType.TIME_WINDOW,
  );

  const [focusedDimensionKeys, setFocusedDimensionKeys] = useState<(string | undefined)[]>([]);
  const [searchValues, setSearchValues] = useState<string[]>([]);

  // Selection for the time dimension (DimensionRangeWizard), matching asset behavior
  const timeDim = timeDimensionIdx !== -1 ? partitionData.dimensions[timeDimensionIdx] : undefined;
  const [selectedTimeKeys, setSelectedTimeKeys] = useState<string[]>(
    () => timeDim?.partitionKeys ?? [],
  );

  const [statusFilters, setStatusFilters] = useQueryPersistedState<AssetCheckPartitionStatus[]>({
    defaults: {status: [...DISPLAYED_STATUSES].sort().join(',')},
    encode: (val) => ({status: [...val].sort().join(',')}),
    decode: (qs) => {
      const status = qs.status;
      if (typeof status === 'string') {
        return status
          .split(',')
          .filter((s): s is AssetCheckPartitionStatus =>
            DISPLAYED_STATUSES.includes(s as AssetCheckPartitionStatus),
          );
      }
      return [...DISPLAYED_STATUSES];
    },
  });

  const updateSearchValue = useCallback((idx: number, value: string) => {
    setSearchValues((prev) => {
      const next = [...prev];
      while (next.length <= idx) {
        next.push('');
      }
      next[idx] = value;
      return next;
    });
  }, []);

  const setFocusedDimensionKey = useCallback(
    (idx: number, key: string | undefined) => {
      setFocusedDimensionKeys((prev) => {
        // Auto-fill upstream dimensions with defaults (matching asset behavior)
        const next: (string | undefined)[] = [];
        for (let ii = 0; ii < idx; ii++) {
          const existing = prev[ii];
          const dim = partitionData.dimensions[ii];
          next.push(existing ?? dim?.partitionKeys[0]);
        }
        if (key) {
          next.push(key);
        }
        return next;
      });
    },
    [partitionData],
  );

  // Build health ranges for the time dimension status bar
  const timeHealthRanges = useMemo(() => {
    if (timeDimensionIdx === -1) {
      return [];
    }
    return buildHealthRangesForDim(partitionData, timeDimensionIdx);
  }, [partitionData, timeDimensionIdx]);

  // Count statuses across all 2D cells for the status filter checkboxes
  const countsByStatus = useMemo(() => {
    const counts: {[key: string]: number} = {
      [AssetCheckPartitionStatus.MISSING]: 0,
      [AssetCheckPartitionStatus.SKIPPED]: 0,
      [AssetCheckPartitionStatus.SUCCEEDED]: 0,
      [AssetCheckPartitionStatus.IN_PROGRESS]: 0,
      [AssetCheckPartitionStatus.FAILED]: 0,
      [AssetCheckPartitionStatus.EXECUTION_FAILED]: 0,
    };

    const dim0Keys = partitionData.dimensions[0]?.partitionKeys ?? [];
    const dim1Keys = partitionData.dimensions[1]?.partitionKeys ?? [];

    for (const k0 of dim0Keys) {
      for (const k1 of dim1Keys) {
        const status = partitionData.statusForPartitionKeys([k0, k1]);
        counts[status] = (counts[status] ?? 0) + 1;
      }
    }

    return counts;
  }, [partitionData]);

  // Keys for each dimension column, sorted and filtered by search
  const keysForDimension = useCallback(
    (idx: number): string[] => {
      const dimension = partitionData.dimensions[idx];
      if (!dimension) {
        return [];
      }

      const searchLower = searchValues[idx]?.toLowerCase().trim() || '';
      let keys = dimension.partitionKeys;

      // For time dimension, filter to selected keys from DimensionRangeWizard
      if (
        idx === timeDimensionIdx &&
        selectedTimeKeys.length < (timeDim?.partitionKeys.length ?? 0)
      ) {
        const selectedSet = new Set(selectedTimeKeys);
        keys = keys.filter((k) => selectedSet.has(k));
      }

      if (searchLower) {
        keys = keys.filter((k) => k.toLowerCase().includes(searchLower));
      }

      // When the other dimension has a focused key, filter by specific cell status
      const otherIdx = idx === 0 ? 1 : 0;
      const otherFocusedKey = focusedDimensionKeys[otherIdx];
      if (otherFocusedKey) {
        keys = keys.filter((k) => {
          const cellKeys = idx === 0 ? [k, otherFocusedKey] : [otherFocusedKey, k];
          const status = partitionData.statusForPartitionKeys(cellKeys);
          return statusFilters.includes(status);
        });
      } else {
        // No focused key in other dimension - filter by aggregate status
        keys = keys.filter((k) => {
          const aggStatus = partitionData.statusForDimAggregate(idx, k);
          return statusFilters.includes(aggStatus);
        });
      }

      const sortType = getDefaultPartitionSort(dimension.type as PartitionDefinitionType);
      return sortPartitionKeys(keys, sortType);
    },
    [
      partitionData,
      searchValues,
      statusFilters,
      focusedDimensionKeys,
      selectedTimeKeys,
      timeDimensionIdx,
      timeDim,
    ],
  );

  const statusForPartitionInDim = useCallback(
    (idx: number, key: string): AssetCheckPartitionStatus[] => {
      const otherIdx = idx === 0 ? 1 : 0;
      const otherFocusedKey = focusedDimensionKeys[otherIdx];
      if (otherFocusedKey) {
        const cellKeys = idx === 0 ? [key, otherFocusedKey] : [otherFocusedKey, key];
        return [partitionData.statusForPartitionKeys(cellKeys)];
      }
      return [partitionData.statusForDimAggregate(idx, key)];
    },
    [partitionData, focusedDimensionKeys],
  );

  // The combined partition key for the detail panel
  const allDimensionsFocused =
    focusedDimensionKeys.length >= 2 && focusedDimensionKeys.every(Boolean);
  const combinedPartitionKey = allDimensionsFocused ? focusedDimensionKeys.join('|') : undefined;

  return (
    <>
      {timeDim && (
        <Box padding={{vertical: 16, horizontal: 24}} border="bottom">
          <DimensionRangeWizard
            dimensionType={timeDim.type as PartitionDefinitionType}
            partitionKeys={timeDim.partitionKeys}
            health={{ranges: timeHealthRanges}}
            selected={selectedTimeKeys}
            setSelected={setSelectedTimeKeys}
            showQuickSelectOptionsForStatuses={false}
          />
        </Box>
      )}
      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        border="bottom"
      >
        <div data-testid={testId('partitions-selected')}>
          {partitionData.dimensions
            .map((d) => d.partitionKeys.length)
            .reduce((a, b) => a * b, 1)
            .toLocaleString()}{' '}
          Partitions
        </div>
        <PartitionStatusCheckboxes
          counts={countsByStatus}
          allowed={DISPLAYED_STATUSES}
          value={statusFilters}
          onChange={setStatusFilters}
          statusToText={assetCheckPartitionStatusToText}
        />
      </Box>

      <Box style={{flex: 1, minHeight: 0, outline: 'none'}} flex={{direction: 'row'}} tabIndex={-1}>
        {partitionData.dimensions.map((dimension, idx) => (
          <Box
            key={dimension.name}
            style={{display: 'flex', flex: 1, paddingRight: 1, minWidth: 200}}
            flex={{direction: 'column'}}
            border="right"
            background={Colors.backgroundLight()}
            data-testid={testId(`partitions-${dimension.name}`)}
          >
            <Box
              border="bottom"
              background={Colors.backgroundDefault()}
              padding={{right: 16, vertical: 8, left: idx === 0 ? 24 : 16}}
            >
              <TextInput
                icon="search"
                fill
                style={{width: '100%'}}
                value={searchValues[idx] || ''}
                onChange={(e) => updateSearchValue(idx, e.target.value)}
                placeholder={
                  dimension.name !== 'default' ? `Filter by ${dimension.name}…` : 'Filter by name…'
                }
                data-testid={testId(`search-${idx}`)}
              />
            </Box>

            <PartitionListSelector
              partitions={keysForDimension(idx)}
              statusForPartition={(key) => statusForPartitionInDim(idx, key)}
              focusedDimensionKey={focusedDimensionKeys[idx]}
              setFocusedDimensionKey={(key) => setFocusedDimensionKey(idx, key)}
              statusesToStyle={assetCheckPartitionStatusesToStyle}
              statusOrder={STATUS_ORDER}
            />
          </Box>
        ))}

        <Box style={{flex: 3, minWidth: 0, overflowY: 'auto'}} flex={{direction: 'column'}}>
          {combinedPartitionKey ? (
            <AssetCheckPartitionDetail
              assetKey={assetKey}
              checkName={checkName}
              partitionKey={combinedPartitionKey}
            />
          ) : (
            <Box
              flex={{direction: 'column', justifyContent: 'center', alignItems: 'center'}}
              style={{height: '100%'}}
            >
              <span style={{color: Colors.textLight()}}>
                {focusedDimensionKeys[0]
                  ? 'Select a partition in the second dimension to view details'
                  : 'Select a partition to view details'}
              </span>
            </Box>
          )}
        </Box>
      </Box>
    </>
  );
};
