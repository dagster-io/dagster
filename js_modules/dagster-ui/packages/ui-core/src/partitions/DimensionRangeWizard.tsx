import {Box, Button, Colors, Icon} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {CreatePartitionDialog} from './CreatePartitionDialog';
import {DimensionRangeInput} from './DimensionRangeInput';
import {OrdinalPartitionSelector} from './OrdinalPartitionSelector';
import {PartitionStatus, PartitionStatusHealthSource} from './PartitionStatus';
import {PartitionDefinitionType} from '../graphql/types';
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
}: {
  selected: string[];
  setSelected: (selected: string[]) => void;
  partitionKeys: string[];
  health: PartitionStatusHealthSource;
  dimensionType: PartitionDefinitionType;
  dynamicPartitionsDefinitionName?: string | null;
  repoAddress?: RepoAddress;
  refetch?: () => Promise<void>;
}) => {
  const isTimeseries = dimensionType === PartitionDefinitionType.TIME_WINDOW;
  const isDynamic = dimensionType === PartitionDefinitionType.DYNAMIC;

  const [showCreatePartition, setShowCreatePartition] = React.useState(false);

  return (
    <>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}} padding={{vertical: 4}}>
        <Box flex={{direction: 'column'}} style={{flex: 1}}>
          {isTimeseries ? (
            <DimensionRangeInput
              value={selected}
              partitionKeys={partitionKeys}
              onChange={setSelected}
              isTimeseries={isTimeseries}
            />
          ) : (
            <OrdinalPartitionSelector
              allPartitions={partitionKeys}
              selectedPartitions={selected}
              setSelectedPartitions={setSelected}
              health={health}
              setShowCreatePartition={setShowCreatePartition}
              isDynamic={isDynamic}
            />
          )}
        </Box>
        {isTimeseries && (
          <Button
            small={true}
            onClick={() => setSelected(partitionKeys.slice(-1))}
            data-testid={testId('latest-partition-button')}
          >
            Latest
          </Button>
        )}
        <Button small={true} onClick={() => setSelected(partitionKeys)}>
          All
        </Button>
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
