import {Box, Button, ButtonLink, Colors, Icon, JoinedButtons} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import * as React from 'react';

import {CreatePartitionDialog} from './CreatePartitionDialog';
import {DimensionRangeInput} from './DimensionRangeInput';
import {OrdinalPartitionSelector} from './OrdinalPartitionSelector';
import {PartitionDateRangeSelector} from './PartitionDateRangeSelector';
import {PartitionStatus, PartitionStatusHealthSource} from './PartitionStatus';
import {convertToPartitionSelection} from './SpanRepresentation';
import {detectDatePartitions, parsePartitionDate} from './isDateFormattedPartitions';
import {AssetPartitionStatus} from '../assets/AssetPartitionStatus';
import {Range, rangesClippedToSelection} from '../assets/usePartitionHealthData';
import {PartitionDefinitionType, RunStatus} from '../graphql/types';
import {useUpdatingRef} from '../hooks/useUpdatingRef';
import {ActivatableButton} from '../runs/ActivatableButton';
import {testId} from '../testing/testId';
import {RepoAddress} from '../workspace/types';

export const DimensionRangeWizard = ({
  selected,
  setSelected,
  partitionKeys,
  health,
  dimensionType,
  dynamicPartitionsDefinitionName,
  repoAddress,
  refetch,
  showQuickSelectOptionsForStatuses,
}: {
  selected: string[];
  setSelected: (selected: string[]) => void;
  partitionKeys: string[];
  health: PartitionStatusHealthSource;
  dimensionType: PartitionDefinitionType;
  dynamicPartitionsDefinitionName?: string | null;
  repoAddress?: RepoAddress;
  refetch?: () => Promise<void>;
  showQuickSelectOptionsForStatuses: boolean;
}) => {
  const isTimeseries = dimensionType === PartitionDefinitionType.TIME_WINDOW;
  const isDynamic = dimensionType === PartitionDefinitionType.DYNAMIC;

  const [showCreatePartition, setShowCreatePartition] = React.useState(false);

  const datePartitionInfo = React.useMemo(
    () => (isTimeseries ? detectDatePartitions(partitionKeys) : null),
    [isTimeseries, partitionKeys],
  );

  const [dateFilter, setDateFilter] = React.useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);

  const filteredPartitionKeys = React.useMemo(() => {
    if (!dateFilter) {
      return partitionKeys;
    }
    const [from, to] = dateFilter;
    return partitionKeys.filter((key) => {
      const parsed = parsePartitionDate(key);
      if (!parsed) {
        return false;
      }
      return (
        (parsed.isAfter(from) || parsed.isSame(from, 'second')) &&
        (parsed.isBefore(to) || parsed.isSame(to, 'second'))
      );
    });
  }, [dateFilter, partitionKeys]);

  // Build a health object with ranges clipped and re-indexed to the filtered key space
  const filteredHealth = React.useMemo((): PartitionStatusHealthSource => {
    if (!dateFilter || !('ranges' in health)) {
      return health;
    }
    // Find the index range in the original partitionKeys that corresponds to filteredPartitionKeys
    const firstFilteredIdx = partitionKeys.indexOf(filteredPartitionKeys[0] ?? '');
    const lastFilteredIdx = partitionKeys.indexOf(
      filteredPartitionKeys[filteredPartitionKeys.length - 1] ?? '',
    );
    if (firstFilteredIdx === -1 || lastFilteredIdx === -1) {
      return health;
    }

    // Clip ranges to the filtered index window
    const startKey = partitionKeys[firstFilteredIdx];
    const endKey = partitionKeys[lastFilteredIdx];
    if (!startKey || !endKey) {
      return health;
    }
    const selection = [
      {
        start: {key: startKey, idx: firstFilteredIdx},
        end: {key: endKey, idx: lastFilteredIdx},
      },
    ];
    const clipped = rangesClippedToSelection(health.ranges, selection);

    // Re-index: shift all indices so they're relative to the filtered array (starting at 0)
    const remapped: Range[] = clipped.map((range) => ({
      ...range,
      start: {key: range.start.key, idx: range.start.idx - firstFilteredIdx},
      end: {key: range.end.key, idx: range.end.idx - firstFilteredIdx},
    }));

    return {ranges: remapped};
  }, [dateFilter, health, partitionKeys, filteredPartitionKeys]);

  const [selectState, setSelectState] = React.useState<
    'all' | 'failed' | 'missing' | 'failed_and_missing' | 'latest' | 'custom'
  >('custom');

  // Track whether the date filter just changed so we can distinguish
  // "filter changed while on custom" from "user cleared their selection".
  const prevFilterRef = React.useRef(dateFilter);
  const filterJustChanged = prevFilterRef.current !== dateFilter;
  React.useEffect(() => {
    prevFilterRef.current = dateFilter;
  }, [dateFilter]);

  // Use refs so that the effect below doesn't re-fire when `health` or
  // `setSelected` get new (but semantically equal) references on each render.
  // The parent (DimensionRangeWizards) passes inline objects/closures for these
  // props, so their identity changes every render cycle.
  const healthRef = useUpdatingRef(health);
  const setSelectedRef = useUpdatingRef(setSelected);

  const applySelectState = React.useCallback(
    (state: typeof selectState, keys: string[]) => {
      switch (state) {
        case 'all':
          setSelectedRef.current(keys);
          break;
        case 'latest':
          setSelectedRef.current(keys.slice(-1));
          break;
        case 'failed':
          setSelectedRef.current(getFailedPartitions(healthRef.current, keys));
          break;
        case 'missing':
          setSelectedRef.current(getMissingPartitions(healthRef.current, keys));
          break;
        case 'failed_and_missing': {
          const failed = getFailedPartitions(healthRef.current, keys);
          const missing = getMissingPartitions(healthRef.current, keys);
          setSelectedRef.current(Array.from(new Set([...failed, ...missing])));
          break;
        }
        case 'custom':
          break;
      }
    },
    [healthRef, setSelectedRef],
  );

  // Re-apply the left-hand select state when the filtered keys change (unless custom).
  // When the date filter changes while on "custom", auto-select all filtered keys so
  // the user isn't left with an empty selection.
  React.useEffect(() => {
    if (selectState === 'custom') {
      if (filterJustChanged) {
        setSelectedRef.current(filteredPartitionKeys);
      }
    } else {
      applySelectState(selectState, filteredPartitionKeys);
    }
  }, [filteredPartitionKeys, selectState, applySelectState, filterJustChanged, setSelectedRef]);

  // When the user directly edits the input or drags on the partition bar while
  // a preset tab is active, switch to Custom and keep their edit.
  const handleUserEdit = React.useCallback(
    (newSelected: string[]) => {
      if (selectState !== 'custom') {
        setSelectState('custom');
      }
      setSelectedRef.current(newSelected);
    },
    [selectState, setSelectedRef],
  );

  const quickSelectButtons = showQuickSelectOptionsForStatuses && (
    <Box flex={{direction: 'row', gap: 8, justifyContent: 'space-between', alignItems: 'center'}}>
      <JoinedButtons>
        {isTimeseries && (
          <ActivatableButton
            as={Button}
            $active={selectState === 'latest'}
            onClick={() => {
              setSelectState('latest');
              applySelectState('latest', filteredPartitionKeys);
            }}
            data-testid={testId('latest-partition-button')}
          >
            Latest
          </ActivatableButton>
        )}
        <ActivatableButton
          as={Button}
          $active={selectState === 'all'}
          onClick={() => {
            setSelectState('all');
            applySelectState('all', filteredPartitionKeys);
          }}
          data-testid={testId('all-partition-button')}
        >
          All
        </ActivatableButton>
        <ActivatableButton
          as={Button}
          $active={selectState === 'failed'}
          onClick={() => {
            setSelectState('failed');
            applySelectState('failed', filteredPartitionKeys);
          }}
        >
          Failed
        </ActivatableButton>
        <ActivatableButton
          as={Button}
          $active={selectState === 'missing'}
          onClick={() => {
            setSelectState('missing');
            applySelectState('missing', filteredPartitionKeys);
          }}
        >
          Missing
        </ActivatableButton>
        <ActivatableButton
          as={Button}
          $active={selectState === 'failed_and_missing'}
          onClick={() => {
            setSelectState('failed_and_missing');
            applySelectState('failed_and_missing', filteredPartitionKeys);
          }}
        >
          Failed and missing
        </ActivatableButton>
        <ActivatableButton
          as={Button}
          $active={selectState === 'custom'}
          onClick={() => {
            setSelectState('custom');
            applySelectState('all', filteredPartitionKeys);
          }}
        >
          Custom
        </ActivatableButton>
      </JoinedButtons>
      {datePartitionInfo && (
        <PartitionDateRangeSelector
          filter={dateFilter}
          onFilterChange={setDateFilter}
          isHighResolution={datePartitionInfo.isHighResolution}
        />
      )}
    </Box>
  );

  return (
    <>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}} padding={{vertical: 4}}>
        <Box flex={{direction: 'column', gap: 8}} style={{flex: 1}}>
          {quickSelectButtons}
          {isTimeseries ? (
            <DimensionRangeInput
              value={selected}
              partitionKeys={filteredPartitionKeys}
              onChange={handleUserEdit}
              isTimeseries={isTimeseries}
              emptyPlaceholder={
                (selectState !== 'custom' && selectState !== 'all') || !!dateFilter
                  ? 'No matching partitions'
                  : undefined
              }
            />
          ) : (
            <OrdinalPartitionSelector
              allPartitions={partitionKeys}
              selectedPartitions={selected}
              setSelectedPartitions={handleUserEdit}
              health={health}
              setShowCreatePartition={setShowCreatePartition}
              isDynamic={isDynamic}
            />
          )}
        </Box>
        {isTimeseries && !showQuickSelectOptionsForStatuses && (
          <Button
            onClick={() => setSelected(partitionKeys.slice(-1))}
            data-testid={testId('latest-partition-button')}
          >
            Latest
          </Button>
        )}
        {!showQuickSelectOptionsForStatuses && (
          <Button
            onClick={() => setSelected(partitionKeys)}
            data-testid={testId('all-partition-button')}
          >
            All
          </Button>
        )}
      </Box>
      <Box margin={{bottom: 8}}>
        {isDynamic && (
          <ButtonLink
            color={Colors.linkDefault()}
            underline="hover"
            onClick={() => {
              setShowCreatePartition(true);
            }}
            data-testid={testId('add-partition-link')}
          >
            <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
              <Icon name="add" size={24} />
              <div>Add a partition</div>
            </Box>
          </ButtonLink>
        )}
        {isTimeseries && (
          <PartitionStatus
            partitionNames={filteredPartitionKeys}
            health={filteredHealth}
            splitPartitions={!isTimeseries}
            selected={selected}
            onSelect={handleUserEdit}
            dateFilterMessage={
              dateFilter && datePartitionInfo ? (
                <Box
                  flex={{direction: 'row', alignItems: 'center', justifyContent: 'center', gap: 6}}
                  color={Colors.textLight()}
                >
                  Showing {filteredPartitionKeys.length} of {partitionKeys.length} partitions
                  <ButtonLink
                    color={Colors.linkDefault()}
                    underline="hover"
                    onClick={() => setDateFilter(null)}
                  >
                    Clear
                  </ButtonLink>
                </Box>
              ) : null
            }
          />
        )}
      </Box>
      {repoAddress && (
        <CreatePartitionDialog
          key={showCreatePartition ? '1' : '0'}
          isOpen={showCreatePartition}
          dynamicPartitionsDefinitionName={dynamicPartitionsDefinitionName}
          repoAddress={repoAddress}
          close={() => {
            setShowCreatePartition(false);
          }}
          refetch={refetch}
          onCreated={(partitionName) => {
            setSelected([...selected, partitionName]);
          }}
        />
      )}
    </>
  );
};

const getMissingPartitions = (health: PartitionStatusHealthSource, partitionKeys: string[]) => {
  if ('ranges' in health) {
    const missingRangeTerms = health.ranges
      .filter((range) => range.value.includes(AssetPartitionStatus.MISSING))
      .map((range) => ({type: 'range' as const, start: range.start.key, end: range.end.key}));
    const missingRangeSelections = convertToPartitionSelection(missingRangeTerms, partitionKeys);
    if (missingRangeSelections instanceof Error) {
      return [];
    }
    return missingRangeSelections.selectedKeys;
  }
  return partitionKeys.filter(
    (key, idx) => health.runStatusForPartitionKey(key, idx) === undefined,
  );
};

const getFailedPartitions = (health: PartitionStatusHealthSource, partitionKeys: string[]) => {
  if ('ranges' in health) {
    const failedRangeTerms = health.ranges
      .filter((range) => range.value.includes(AssetPartitionStatus.FAILED))
      .map((range) => ({type: 'range' as const, start: range.start.key, end: range.end.key}));

    const failedRangeSelections = convertToPartitionSelection(failedRangeTerms, partitionKeys);
    if (failedRangeSelections instanceof Error) {
      return [];
    }
    return failedRangeSelections.selectedKeys;
  }
  return partitionKeys.filter(
    (key, idx) => health.runStatusForPartitionKey(key, idx) === RunStatus.FAILURE,
  );
};
