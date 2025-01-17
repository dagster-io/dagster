// eslint-disable-next-line no-restricted-imports
import {
  Body2,
  Box,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  Spinner,
} from '@dagster-io/ui-components';
import {memo, useCallback, useMemo, useState} from 'react';

import {
  DeleteDynamicPartitionsMutation,
  DeleteDynamicPartitionsMutationVariables,
} from './types/DeleteDynamicPartitionsDialog.types';
import {usePartitionHealthData} from './usePartitionHealthData';
import {RefetchQueriesFunction, gql, useMutation} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {AssetKeyInput, PartitionDefinitionType} from '../graphql/types';
import {OrdinalPartitionSelector} from '../partitions/OrdinalPartitionSelector';
import {RepoAddress} from '../workspace/types';

export interface DeleteDynamicPartitionsDialogProps {
  assetKey: AssetKeyInput;
  repoAddress: RepoAddress;
  partitionsDefName: string;
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
  requery?: RefetchQueriesFunction;
}

export const DeleteDynamicPartitionsDialog = memo((props: DeleteDynamicPartitionsDialogProps) => {
  return (
    <Dialog
      isOpen={props.isOpen}
      title={`Delete ${props.partitionsDefName} partitions`}
      onClose={props.onClose}
      style={{width: '50vw', minWidth: 500, maxWidth: 700}}
    >
      <DeleteDynamicPartitionsDialogInner {...props} />
    </Dialog>
  );
});

export const DeleteDynamicPartitionsDialogInner = memo(
  ({
    repoAddress,
    assetKey,
    partitionsDefName,
    onClose,
    onComplete,
    requery,
  }: DeleteDynamicPartitionsDialogProps) => {
    const [deleting, setDeleting] = useState(false);
    const [result, setResult] = useState<
      DeleteDynamicPartitionsMutation['deleteDynamicPartitions'] | undefined
    >();
    const [selectedPartitions, setSelectedPartitions] = useState<string[]>([]);
    const [health] = usePartitionHealthData([assetKey]);

    const dynamicHealth = health?.dimensions.find(
      (d) => d.type === PartitionDefinitionType.DYNAMIC,
    );

    const [deletePartitions] = useMutation<
      DeleteDynamicPartitionsMutation,
      DeleteDynamicPartitionsMutationVariables
    >(DELETE_DYNAMIC_PARTITIONS_MUTATION, {refetchQueries: requery});

    const onDelete = useCallback(
      async (partitionKeys: string[]) => {
        setDeleting(true);
        const resp = await deletePartitions({
          variables: {
            repositorySelector: {
              repositoryLocationName: repoAddress.location,
              repositoryName: repoAddress.name,
            },
            partitionsDefName,
            partitionKeys,
          },
        });
        setResult(resp.data?.deleteDynamicPartitions);
        setDeleting(false);
        onComplete?.();
      },
      [deletePartitions, onComplete, partitionsDefName, repoAddress.location, repoAddress.name],
    );

    const content = useMemo(() => {
      if (result) {
        return (
          <Box flex={{direction: 'column'}}>
            {result.__typename === 'DeleteDynamicPartitionsSuccess' ? (
              <Body2>
                The selected partitions of <strong>{partitionsDefName}</strong> and associated
                materializations have been deleted.
              </Body2>
            ) : (
              <PythonErrorInfo error={result} />
            )}
          </Box>
        );
      }
      if (deleting) {
        return (
          <Box flex={{gap: 8, direction: 'column'}}>
            <div>Wiping...</div>
          </Box>
        );
      }
      return (
        <Box flex={{direction: 'column', gap: 6}}>
          <Body2>
            Select partition keys of the <strong>{partitionsDefName}</strong> partition definition
            to delete.
          </Body2>
          {health && dynamicHealth ? (
            <OrdinalPartitionSelector
              allPartitions={dynamicHealth?.partitionKeys}
              selectedPartitions={selectedPartitions}
              setSelectedPartitions={setSelectedPartitions}
              health={health}
              isDynamic={true}
            />
          ) : (
            <Spinner purpose="section" />
          )}
          <Body2 style={{marginTop: 10}}>
            Deleting partitions impacts all assets that share this partition definition.
            Materialization events for these partitions will be wiped.{' '}
            <strong>This action cannot be undone.</strong>
          </Body2>
        </Box>
      );
    }, [deleting, dynamicHealth, health, partitionsDefName, result, selectedPartitions]);

    return (
      <>
        <DialogBody>{content}</DialogBody>
        <DialogFooter topBorder>
          <Button intent={result ? 'primary' : 'none'} onClick={onClose}>
            {result ? 'Done' : 'Cancel'}
          </Button>
          {result ? null : (
            <Button
              intent="danger"
              onClick={() => onDelete(selectedPartitions)}
              disabled={deleting || selectedPartitions.length === 0}
              loading={deleting}
            >
              {selectedPartitions.length === 1
                ? 'Delete 1 partition'
                : `Delete ${selectedPartitions.length} partitions`}
            </Button>
          )}
        </DialogFooter>
      </>
    );
  },
);

export const DELETE_DYNAMIC_PARTITIONS_MUTATION = gql`
  mutation DeleteDynamicPartitionsMutation(
    $partitionKeys: [String!]!
    $partitionsDefName: String!
    $repositorySelector: RepositorySelector!
  ) {
    deleteDynamicPartitions(
      partitionKeys: $partitionKeys
      partitionsDefName: $partitionsDefName
      repositorySelector: $repositorySelector
    ) {
      ... on DeleteDynamicPartitionsSuccess {
        __typename
      }
      ... on UnauthorizedError {
        message
        __typename
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
