import {gql, useMutation} from '@apollo/client';
import {
  Box,
  Button,
  Checkbox,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Menu,
  MenuDivider,
  MenuItem,
  Mono,
  Spinner,
  TagSelector,
  TextInput,
} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {StateDot} from '../assets/AssetPartitionList';
import {isTimeseriesPartition} from '../assets/MultipartitioningSupport';
import {partitionStateAtIndex, Range} from '../assets/usePartitionHealthData';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {DimensionRangeInput} from './DimensionRangeInput';
import {PartitionStatusHealthSource, PartitionStatus} from './PartitionStatus';
import {
  AddDynamicPartitionMutation,
  AddDynamicPartitionMutationVariables,
} from './types/DimensionRangeWizard.types';

export const DimensionRangeWizard: React.FC<{
  selected: string[];
  setSelected: (selected: string[]) => void;
  partitionKeys: string[];
  health: PartitionStatusHealthSource;
  isDynamic?: boolean;
  partitionDefinitionName?: string | null;
  repoAddress?: RepoAddress;
  refetch?: () => void;
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
          selected={selected}
          setSelected={setSelected}
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
  setSelected:
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
const CreatePartitionDialog = ({
  isOpen,
  partitionDefinitionName,
  close,
  repoAddress,
  refetch,
  selected,
  setSelected
}: {
  isOpen: boolean;
  partitionDefinitionName?: string | null;
  close: () => void;
  repoAddress: RepoAddress;
  refetch?: () => void;
  selected: string[];
  setSelected: (selected: string[]) => void;
}) => {
  const [partitionName, setPartitionName] = React.useState('');

  const [createPartition] = useMutation<
    AddDynamicPartitionMutation,
    AddDynamicPartitionMutationVariables
  >(CREATE_PARTITION_MUTATION);

  const [isSaving, setIsSaving] = React.useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    const result = await createPartition({
      variables: {
        repositorySelector: repoAddressToSelector(repoAddress),
        partitionsDefName: partitionDefinitionName || '',
        partitionKey: partitionName,
      },
    });
    setIsSaving(false);

    const data = result.data?.addDynamicPartition;
    switch (data?.__typename) {
      case 'PythonError': {
        showCustomAlert({
          title: 'Could not create environment variable',
          body: <PythonErrorInfo error={data} />,
        });
        break;
      }
      case 'DuplicateDynamicPartitionError': {
        showCustomAlert({
          title: 'Could not add partition',
          body: 'A partition this name already exists.',
        });
        break;
      }
      case 'UnauthorizedError': {
        showCustomAlert({
          title: 'Could not add partition',
          body: 'You do not have permission to do this.',
        });
        break;
      }
      case 'AddDynamicPartitionSuccess': {
        refetch?.();
        setSelected([...selected, partitionName]);
        close();
        break;
      }
      default: {
        showCustomAlert({
          title: 'Could not add partition',
          body: 'An unknown error occurred.',
        });
        break;
      }
    }
  };
  return (
    <Dialog
      isOpen={isOpen}
      canEscapeKeyClose
      canOutsideClickClose
      title={
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <Icon name="add_circle" size={24} />
          <div>
            Add a partition
            {partitionDefinitionName ? (
              <>
                {' '}
                for <Mono>{partitionDefinitionName}</Mono>
              </>
            ) : (
              ''
            )}
          </div>
        </Box>
      }
    >
      <DialogBody>
        <Box flex={{direction: 'column', gap: 6}}>
          <div>Partition name</div>
          <TextInput
            rightElement={isSaving ? <Spinner purpose="body-text" /> : undefined}
            disabled={isSaving}
            placeholder="name"
            value={partitionName}
            onChange={(e) => setPartitionName(e.target.value)}
            onKeyPress={(e) => {
              if (e.code === 'Enter') {
                handleSave();
              }
            }}
          />
        </Box>
      </DialogBody>
      <DialogFooter>
        <Button onClick={close}>Cancel</Button>
        <Button intent="primary" onClick={handleSave}>
          Save
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

export const CREATE_PARTITION_MUTATION = gql`
  mutation AddDynamicPartitionMutation(
    $partitionsDefName: String!
    $partitionKey: String!
    $repositorySelector: RepositorySelector!
  ) {
    addDynamicPartition(
      partitionsDefName: $partitionsDefName
      partitionKey: $partitionKey
      repositorySelector: $repositorySelector
    ) {
      __typename
      ... on AddDynamicPartitionSuccess {
        partitionsDefName
        partitionKey
      }
      ... on PythonError {
        message
        stack
      }
      ... on UnauthorizedError {
        message
      }
    }
  }
`;
