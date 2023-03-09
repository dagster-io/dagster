import {
  Box,
  Button,
  Checkbox,
  Colors,
  Icon,
  Menu,
  MenuDivider,
  MenuItem,
  TagSelector,
} from '@dagster-io/ui';
import qs from 'qs';
import * as React from 'react';
import styled from 'styled-components/macro';

import {StateDot} from '../assets/AssetPartitionList';
import {isTimeseriesPartition} from '../assets/MultipartitioningSupport';
import {partitionStateAtIndex, Range} from '../assets/usePartitionHealthData';
import {RepoAddress} from '../workspace/types';

import {CreatePartitionDialog} from './CreatePartitionDialog';
import {DimensionRangeInput} from './DimensionRangeInput';
import {PartitionStatusHealthSource, PartitionStatus} from './PartitionStatus';

export const DimensionRangeWizard: React.FC<{
  selected: string[];
  setSelected: (selected: string[]) => void;
  partitionKeys: string[];
  health: PartitionStatusHealthSource;
  isDynamic?: boolean;
  partitionDefinitionName?: string | null;
  repoAddress?: RepoAddress;
  refetch?: () => Promise<void>;
}> = ({
  selected,
  setSelected,
  partitionKeys,
  health,
  isDynamic = false,
  partitionDefinitionName,
  repoAddress,
  refetch,
}) => {
  const isTimeseries = isTimeseriesPartition(partitionKeys[0]);

  const [showCreatePartition, setShowCreatePartition] = React.useState(false);

  const didSetInitialPartition = React.useRef(false);
  React.useEffect(() => {
    if (didSetInitialPartition.current || !partitionKeys.length) {
      return;
    }
    didSetInitialPartition.current = true;
    const query = qs.parse(window.location.search, {ignoreQueryPrefix: true});
    const partition = query.partition as string;
    if (partition && partitionKeys.includes(partition)) {
      setSelected([partition]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [partitionKeys]);

  return (
    <>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}} padding={{vertical: 4}}>
        <Box flex={{direction: 'column'}} style={{flex: 1}}>
          {isDynamic ? (
            <DynamicPartitionSelector
              allPartitions={partitionKeys}
              selectedPartitions={selected}
              setSelectedPartitions={setSelected}
              health={health}
              setShowCreatePartition={setShowCreatePartition}
            />
          ) : (
            <DimensionRangeInput
              value={selected}
              partitionKeys={partitionKeys}
              onChange={setSelected}
              isTimeseries={isTimeseries}
            />
          )}
        </Box>
        {isTimeseries && !isDynamic && (
          <Button small={true} onClick={() => setSelected(partitionKeys.slice(-1))}>
            Latest
          </Button>
        )}
        <Button small={true} onClick={() => setSelected(partitionKeys)}>
          All
        </Button>
      </Box>
      <Box margin={{bottom: 8}}>
        {isDynamic ? (
          <LinkText
            flex={{direction: 'row', alignItems: 'center', gap: 8}}
            onClick={() => {
              setShowCreatePartition(true);
            }}
          >
            <StyledIcon name="add" size={24} />
            <div>Add a partition</div>
          </LinkText>
        ) : (
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
          partitionDefinitionName={partitionDefinitionName}
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

const DynamicPartitionSelector: React.FC<{
  allPartitions: string[];
  selectedPartitions: string[];
  setSelectedPartitions: (tags: string[]) => void;
  health: PartitionStatusHealthSource;
  setShowCreatePartition: (show: boolean) => void;
}> = ({
  allPartitions,
  selectedPartitions,
  setSelectedPartitions,
  setShowCreatePartition,
  health,
}) => {
  const isAllSelected =
    allPartitions.length === selectedPartitions.length && allPartitions.length > 0;

  const statusForPartitionKey = (partitionKey: string) => {
    const index = allPartitions.indexOf(partitionKey);
    if ('ranges' in health) {
      return partitionStateAtIndex(health.ranges as Range[], index);
    } else {
      return health.partitionStateForKey(partitionKey, index);
    }
  };

  return (
    <>
      <TagSelector
        allTags={allPartitions}
        selectedTags={selectedPartitions}
        setSelectedTags={setSelectedPartitions}
        placeholder="Select a partition or create one"
        renderDropdownItem={(tag, dropdownItemProps) => {
          return (
            <label>
              <MenuItem
                tagName="div"
                text={
                  <Box flex={{alignItems: 'center', gap: 12}}>
                    <Checkbox
                      checked={dropdownItemProps.selected}
                      onChange={dropdownItemProps.toggle}
                    />
                    <StateDot state={statusForPartitionKey(tag)} />
                    <span>{tag}</span>
                  </Box>
                }
              />
            </label>
          );
        }}
        renderDropdown={(dropdown, {width}) => {
          const toggleAll = () => {
            if (isAllSelected) {
              setSelectedPartitions([]);
            } else {
              setSelectedPartitions(allPartitions);
            }
          };
          return (
            <Menu style={{width}}>
              <Box padding={4}>
                <Box flex={{direction: 'column'}}>
                  <MenuItem
                    tagName="div"
                    text={
                      <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
                        <StyledIcon name="add" size={24} />
                        <span>Add partition</span>
                      </Box>
                    }
                    onClick={() => {
                      setShowCreatePartition(true);
                    }}
                  />
                </Box>
                <MenuDivider />
                {allPartitions.length ? (
                  <>
                    <label>
                      <MenuItem
                        tagName="div"
                        text={
                          <Box flex={{alignItems: 'center', gap: 12}}>
                            <Checkbox checked={isAllSelected} onChange={toggleAll} />
                            <span>Select all ({allPartitions.length})</span>
                          </Box>
                        }
                      />
                    </label>
                    {dropdown}
                  </>
                ) : (
                  <div style={{padding: '6px 6px 0px 6px', color: Colors.Gray700}}>
                    No matching partitions found
                  </div>
                )}
              </Box>
            </Menu>
          );
        }}
        renderTagList={(tags) => {
          if (tags.length > 4) {
            return <span>{tags.length} partitions selected</span>;
          }
          return tags;
        }}
      />
    </>
  );
};

const StyledIcon = styled(Icon)`
  font-weight: 500;
`;

const LinkText = styled(Box)`
  color: ${Colors.Link};
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
