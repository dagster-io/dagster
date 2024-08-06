import {RefetchQueriesFunction} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {ProgressBar} from '@blueprintjs/core';
import {Body1, Box, Button, Dialog, DialogBody, DialogFooter} from '@dagster-io/ui-components';
import {memo, useMemo} from 'react';

import {asAssetPartitionRangeInput} from './asInput';
import {useWipeAssets} from './useWipeAssets';
import {AssetKeyInput} from '../graphql/types';
import {NavigationBlock} from '../runs/NavigationBlock';
import {numberFormatter} from '../ui/formatters';
import {RepoAddress} from '../workspace/types';

export interface DeleteDynamicPartitionsDialogProps {
  repo: RepoAddress;
  partitionsDefName: string;
  assetKey: AssetKeyInput;
}

export const DeleteDynamicPartitionsDialog = memo(
  (props: {
    isOpen: boolean;
    onClose: () => void;
    onComplete?: () => void;
    requery?: RefetchQueriesFunction;
  }) => {
    return (
      <Dialog
        isOpen={props.isOpen}
        title={`Delete ${props.partitionsDefName} partitions`}
        onClose={props.onClose}
        style={{width: '80vw', maxWidth: '1200px', minWidth: '600px'}}
      >
        <DeleteDynamicPartitionsModalInner {...props} />
      </Dialog>
    );
  },
);

export const DeleteDynamicPartitionsModalInner = memo(
  ({
    repo,
    partitionsDefName,
    onClose,
    onComplete,
    requery,
  }: {
    repo: {name: string; location: {name: string}};
    partitionsDefName: string;
    onClose: () => void;
    onComplete?: () => void;
    requery?: RefetchQueriesFunction;
  }) => {
    const {wipeAssets, isWiping, isDone, wipedCount, failedCount} = useWipeAssets({
      refetchQueries: requery,
      onClose,
      onComplete,
    });

    const health = use;
    const content = useMemo(() => {
      if (isDone) {
        return (
          <Box flex={{direction: 'column'}}>
            {wipedCount ? <Body1>{numberFormatter.format(wipedCount)} Wiped</Body1> : null}
            {failedCount ? <Body1>{numberFormatter.format(failedCount)} Failed</Body1> : null}
          </Box>
        );
      } else if (!isWiping) {
        return (
          <Box>
            <div>
              Choose partitions to delete below. Materialization events for these partitions will
              also be wiped.
            </div>
            <OrdinalPartitionSelector />
            <strong>This action cannot be undone.</strong>
          </Box>
        );
      }
      const value = assetKeys.length > 0 ? (wipedCount + failedCount) / assetKeys.length : 1;
      return (
        <Box flex={{gap: 8, direction: 'column'}}>
          <div>Wiping...</div>
          <ProgressBar intent="primary" value={Math.max(0.1, value)} animate={value < 1} />
          <NavigationBlock message="Wiping in progress, please do not navigate away yet." />
        </Box>
      );
    }, [isDone, isWiping, assetKeys, wipedCount, failedCount]);

    return (
      <>
        <DialogBody>{content}</DialogBody>
        <DialogFooter topBorder>
          <Button intent={isDone ? 'primary' : 'none'} onClick={onClose}>
            {isDone ? 'Done' : 'Cancel'}
          </Button>
          {isDone ? null : (
            <Button
              intent="danger"
              onClick={() => wipeAssets(assetKeys.map((key) => asAssetPartitionRangeInput(key)))}
              disabled={isWiping}
              loading={isWiping}
            >
              Wipe
            </Button>
          )}
        </DialogFooter>
      </>
    );
  },
);
