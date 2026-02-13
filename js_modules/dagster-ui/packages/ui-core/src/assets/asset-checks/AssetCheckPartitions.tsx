import {Box, Button, Colors, NonIdealState, TextInput} from '@dagster-io/ui-components';
import {useCallback, useMemo, useState} from 'react';

import {AssetCheckPartitionDetail} from './AssetCheckPartitionDetail';
import {
  AssetCheckPartitionStatus,
  assetCheckPartitionStatusToText,
  assetCheckPartitionStatusesToStyle,
} from './AssetCheckPartitionStatus';
import {AssetCheckPartitionStatusBar} from './AssetCheckPartitionStatusBar';
import {AssetCheckPartitionData, useAssetCheckPartitionData} from './useAssetCheckPartitionData';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {testId} from '../../testing/testId';
import {PartitionListSelector} from '../PartitionListSelector';
import {PartitionStatusCheckboxes} from '../PartitionStatusCheckboxes';
import {getDefaultPartitionSort, sortPartitionKeys} from '../partitionSortUtils';
import {AssetKey} from '../types';

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
  const [selectedPartitionKeys, setSelectedPartitionKeys] = useState<string[]>([]);
  const [searchValue, setSearchValue] = useState('');

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

  const {filteredPartitions, countsByStatus} = useMemo(() => {
    const counts: {[key: string]: number} = {
      [AssetCheckPartitionStatus.MISSING]: 0,
      [AssetCheckPartitionStatus.SKIPPED]: 0,
      [AssetCheckPartitionStatus.SUCCEEDED]: 0,
      [AssetCheckPartitionStatus.IN_PROGRESS]: 0,
      [AssetCheckPartitionStatus.FAILED]: 0,
      [AssetCheckPartitionStatus.EXECUTION_FAILED]: 0,
    };

    const allPartitions = partitionData.partitions;
    const filtered = allPartitions.filter((partition) => {
      if (selectedPartitionKeys.length > 0 && !selectedPartitionKeys.includes(partition)) {
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
  }, [partitionData, statusFilters, searchValue, selectedPartitionKeys]);

  const sortedAndFilteredPartitions = useMemo(() => {
    if (partitionData.dimensions.length === 0) {
      return filteredPartitions;
    }

    const firstDimension = partitionData.dimensions[0];
    if (!firstDimension) {
      return filteredPartitions;
    }

    const dimensionType = firstDimension.type;
    const sortType = getDefaultPartitionSort(dimensionType as any);
    return sortPartitionKeys(filteredPartitions, sortType);
  }, [filteredPartitions, partitionData]);

  const statusForPartition = (dimensionKey: string): AssetCheckPartitionStatus[] => {
    return [partitionData.statusForPartition(dimensionKey)];
  };

  return (
    <>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        border="bottom"
      >
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <div data-testid={testId('partitions-selected')}>
            {sortedAndFilteredPartitions.length.toLocaleString()}{' '}
            {selectedPartitionKeys.length > 0 ? 'of' : 'Partitions'}
            {selectedPartitionKeys.length > 0 && (
              <> {partitionData.partitions.length.toLocaleString()} partitions</>
            )}
          </div>
          {selectedPartitionKeys.length > 0 && (
            <Button
              onClick={() => {
                setSelectedPartitionKeys([]);
                setFocusedPartitionKey(undefined);
              }}
            >
              Clear selection
            </Button>
          )}
        </Box>
        <PartitionStatusCheckboxes
          counts={countsByStatus}
          allowed={DISPLAYED_STATUSES}
          value={statusFilters}
          onChange={setStatusFilters}
          statusToText={assetCheckPartitionStatusToText}
        />
      </Box>

      {partitionData.partitions.length > 0 && partitionData.dimensions.length > 0 && (
        <Box padding={{vertical: 16, horizontal: 24}} border="bottom">
          <AssetCheckPartitionStatusBar
            partitionKeys={partitionData.partitions}
            statusForPartition={partitionData.statusForPartition}
            selected={selectedPartitionKeys}
            onSelect={(selectedKeys) => {
              setSelectedPartitionKeys(selectedKeys);
              if (selectedKeys.length > 0) {
                setFocusedPartitionKey(selectedKeys[0]);
              }
            }}
            splitPartitions={partitionData.dimensions[0]?.type !== 'TIME_WINDOW'}
          />
        </Box>
      )}

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
  const [focusedDimensionKeys, setFocusedDimensionKeys] = useState<(string | undefined)[]>([]);
  const [searchValues, setSearchValues] = useState<string[]>([]);

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

  const setFocusedDimensionKey = useCallback((idx: number, key: string | undefined) => {
    setFocusedDimensionKeys((prev) => {
      const next = [...prev];
      while (next.length <= idx) {
        next.push(undefined);
      }
      next[idx] = key;
      // Clear downstream selections when an upstream dimension changes
      for (let i = idx + 1; i < next.length; i++) {
        next[i] = undefined;
      }
      return next;
    });
  }, []);

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

      if (searchLower) {
        keys = keys.filter((k) => k.toLowerCase().includes(searchLower));
      }

      // For dim1, only show keys that match the status filters when scoped to selected dim0
      if (idx === 1 && focusedDimensionKeys[0]) {
        const dim0Key = focusedDimensionKeys[0];
        keys = keys.filter((k1) => {
          const status = partitionData.statusForPartitionKeys([dim0Key, k1]);
          return statusFilters.includes(status);
        });
      }

      // For dim0, filter by aggregate status
      if (idx === 0) {
        keys = keys.filter((k0) => {
          const aggStatus = partitionData.statusForDim0Aggregate(k0);
          return statusFilters.includes(aggStatus);
        });
      }

      const sortType = getDefaultPartitionSort(dimension.type as any);
      return sortPartitionKeys(keys, sortType);
    },
    [partitionData, searchValues, statusFilters, focusedDimensionKeys],
  );

  const statusForPartitionInDim = useCallback(
    (idx: number, key: string): AssetCheckPartitionStatus[] => {
      if (idx === 0) {
        return [partitionData.statusForDim0Aggregate(key)];
      }
      if (idx === 1 && focusedDimensionKeys[0]) {
        return [partitionData.statusForPartitionKeys([focusedDimensionKeys[0], key])];
      }
      return [AssetCheckPartitionStatus.MISSING];
    },
    [partitionData, focusedDimensionKeys],
  );

  // The combined partition key for the detail panel
  const allDimensionsFocused =
    focusedDimensionKeys.length >= 2 && focusedDimensionKeys.every(Boolean);
  const combinedPartitionKey = allDimensionsFocused ? focusedDimensionKeys.join('|') : undefined;

  return (
    <>
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
              <Box style={{color: Colors.textLight()}}>
                {focusedDimensionKeys[0]
                  ? 'Select a partition in the second dimension to view details'
                  : 'Select a partition to view details'}
              </Box>
            </Box>
          )}
        </Box>
      </Box>
    </>
  );
};
