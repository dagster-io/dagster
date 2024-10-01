// eslint-disable-next-line no-restricted-imports
import {ProgressBar} from '@blueprintjs/core';
import {
  Body1,
  Box,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  Group,
  ifPlural,
} from '@dagster-io/ui-components';
import {memo, useMemo} from 'react';

import {VirtualizedSimpleAssetKeyList} from './VirtualizedSimpleAssetKeyList';
import {asAssetPartitionRangeInput} from './asInput';
import {useWipeAssets} from './useWipeAssets';
import {RefetchQueriesFunction} from '../apollo-client';
import {AssetKeyInput} from '../graphql/types';
import {NavigationBlock} from '../runs/NavigationBlock';
import {numberFormatter} from '../ui/formatters';

export const AssetWipeDialog = memo(
  (props: {
    assetKeys: AssetKeyInput[];
    isOpen: boolean;
    onClose: () => void;
    onComplete?: () => void;
    requery?: RefetchQueriesFunction;
  }) => {
    return (
      <Dialog
        isOpen={props.isOpen}
        title="Wipe materializations"
        onClose={props.onClose}
        style={{width: '80vw', maxWidth: '1200px', minWidth: '600px'}}
      >
        <AssetWipeDialogInner {...props} />
      </Dialog>
    );
  },
);

export const AssetWipeDialogInner = memo(
  ({
    assetKeys,
    onClose,
    onComplete,
    requery,
  }: {
    assetKeys: AssetKeyInput[];
    onClose: () => void;
    onComplete?: () => void;
    requery?: RefetchQueriesFunction;
  }) => {
    const {wipeAssets, isWiping, isDone, wipedCount, failedCount} = useWipeAssets({
      refetchQueries: requery,
      onClose,
      onComplete,
    });

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
          <Group direction="column" spacing={16}>
            <div>
              Are you sure you want to wipe materializations for{' '}
              {numberFormatter.format(assetKeys.length)}{' '}
              {ifPlural(assetKeys.length, 'asset', 'assets')}?
            </div>
            <VirtualizedSimpleAssetKeyList assetKeys={assetKeys} style={{maxHeight: '50vh'}} />
            <div>
              Assets defined only by their historical materializations will disappear from the Asset
              Catalog. Software-defined assets will remain unless their definition is also deleted.
            </div>
            <strong>This action cannot be undone.</strong>
          </Group>
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
