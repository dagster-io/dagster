import {Box, Colors, NonIdealState, TextInput} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {AssetCheckPartitionDetail} from './AssetCheckPartitionDetail';
import {
  AssetCheckPartitionStatus,
  assetCheckPartitionStatusToText,
  assetCheckPartitionStatusesToStyle,
} from './AssetCheckPartitionStatus';
import {useAssetCheckPartitionData} from './useAssetCheckPartitionData';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {testId} from '../../testing/testId';
import {PartitionListSelector} from '../PartitionListSelector';
import {PartitionStatusCheckboxes} from '../PartitionStatusCheckboxes';
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
  const [focusedPartitionKey, setFocusedPartitionKey] = useState<string | undefined>();
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

  // Calculate partition counts by status
  const {filteredPartitions, countsByStatus} = useMemo(() => {
    if (!partitionData) {
      return {filteredPartitions: [], countsByStatus: {}};
    }

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
      if (searchValue && !partition.toLowerCase().includes(searchValue.toLowerCase())) {
        return false;
      }

      const primaryStatus = partitionData.statusForPartition(partition);

      counts[primaryStatus] = !counts[primaryStatus] ? 1 : counts[primaryStatus] + 1;
      return statusFilters.includes(primaryStatus);
    });

    return {filteredPartitions: filtered, countsByStatus: counts};
  }, [partitionData, statusFilters, searchValue]);

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

  const statusForPartition = (dimensionKey: string): AssetCheckPartitionStatus[] => {
    return [partitionData.statusForPartition(dimensionKey)];
  };

  return (
    <>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between'}}
        border="bottom"
      >
        <div data-testid={testId('partitions-selected')}>
          {filteredPartitions.length.toLocaleString()} Partitions Selected
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
              placeholder="Filter partitions"
            />
          </Box>

          <PartitionListSelector
            partitions={filteredPartitions}
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
