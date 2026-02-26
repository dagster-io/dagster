import {Box, Button, Colors, Icon, JoinedButtons} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {CreatePartitionDialog} from './CreatePartitionDialog';
import {DimensionRangeInput} from './DimensionRangeInput';
import {OrdinalPartitionSelector} from './OrdinalPartitionSelector';
import {PartitionStatus, PartitionStatusHealthSource} from './PartitionStatus';
import {convertToPartitionSelection} from './SpanRepresentation';
import {AssetPartitionStatus} from '../assets/AssetPartitionStatus';
import {PartitionDefinitionType, RunStatus} from '../graphql/types';
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

  // For multi-dimensional partitions, this is set to false because filtering by failed or missing
  // partitions only makes sense when applied across all dimensions simultaneously.
  // This dialog is also used to backfill jobs and in that case we also set it to false.
  showQuickSelectOptionsForStatuses: boolean;
}) => {
  const isTimeseries = dimensionType === PartitionDefinitionType.TIME_WINDOW;
  const isDynamic = dimensionType === PartitionDefinitionType.DYNAMIC;

  const [showCreatePartition, setShowCreatePartition] = React.useState(false);

  const [selectState, setSelectState] = React.useState<
    'all' | 'failed' | 'missing' | 'failed_and_missing' | 'latest' | 'custom'
  >('custom');

  const quickSelectButtons = showQuickSelectOptionsForStatuses && (
    <Box flex={{direction: 'row', gap: 8}}>
      <JoinedButtons>
        {isTimeseries && (
          <ActivatableButton
            as={Button}
            $active={selectState === 'latest'}
            onClick={() => {
              setSelectState('latest');
              setSelected(partitionKeys.slice(-1));
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
            setSelected(partitionKeys);
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
            setSelected(getFailedPartitions(health, partitionKeys));
          }}
        >
          All failed
        </ActivatableButton>
        <ActivatableButton
          as={Button}
          $active={selectState === 'missing'}
          onClick={() => {
            setSelectState('missing');
            setSelected(getMissingPartitions(health, partitionKeys));
          }}
        >
          All missing
        </ActivatableButton>
        <ActivatableButton
          as={Button}
          $active={selectState === 'failed_and_missing'}
          onClick={() => {
            setSelectState('failed_and_missing');
            const failedPartitions = getFailedPartitions(health, partitionKeys);
            const missingPartitions = getMissingPartitions(health, partitionKeys);
            setSelected(Array.from(new Set([...failedPartitions, ...missingPartitions])));
          }}
        >
          All failed and missing
        </ActivatableButton>
        <ActivatableButton
          as={Button}
          $active={selectState === 'custom'}
          onClick={() => {
            setSelectState('custom');
            setSelected(partitionKeys);
          }}
        >
          Custom
        </ActivatableButton>
      </JoinedButtons>
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
              partitionKeys={partitionKeys}
              onChange={setSelected}
              isTimeseries={isTimeseries}
              disabled={selectState !== 'custom'}
            />
          ) : (
            <OrdinalPartitionSelector
              allPartitions={partitionKeys}
              selectedPartitions={selected}
              setSelectedPartitions={setSelected}
              health={health}
              setShowCreatePartition={setShowCreatePartition}
              isDynamic={isDynamic}
              disabled={selectState !== 'custom'}
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
          <LinkText
            flex={{direction: 'row', alignItems: 'center', gap: 8}}
            onClick={() => {
              setShowCreatePartition(true);
            }}
            data-testid={testId('add-partition-link')}
          >
            <StyledIcon name="add" size={24} />
            <div>Add a partition</div>
          </LinkText>
        )}
        {isTimeseries && (
          <PartitionStatus
            partitionNames={partitionKeys}
            health={health}
            splitPartitions={!isTimeseries}
            selected={selected}
            onSelect={setSelected}
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

const LinkText = styled(Box)`
  color: ${Colors.linkDefault()};
  cursor: pointer;
  &:hover {
    text-decoration: underline;
  }
  > * {
    height: 24px;
    align-content: center;
    line-height: 24px;
  }
`;

const StyledIcon = styled(Icon)`
  font-weight: 500;
`;
