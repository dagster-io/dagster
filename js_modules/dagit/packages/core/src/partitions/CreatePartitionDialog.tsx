import {gql, useMutation} from '@apollo/client';
import {
  Box,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Mono,
  Spinner,
  TextInput,
} from '@dagster-io/ui';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {
  AddDynamicPartitionMutation,
  AddDynamicPartitionMutationVariables,
} from './types/CreatePartitionDialog.types';

export const CreatePartitionDialog = ({
  isOpen,
  partitionDefinitionName,
  close,
  repoAddress,
  refetch,
  selected,
  setSelected,
}: {
  isOpen: boolean;
  partitionDefinitionName?: string | null;
  close: () => void;
  repoAddress: RepoAddress;
  refetch?: () => Promise<void>;
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
