import {RefetchQueriesFunction, gql, useMutation} from '@apollo/client';
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
import {useVirtualizer} from '@tanstack/react-virtual';
import {memo, useLayoutEffect, useMemo, useRef, useState} from 'react';

import {asAssetPartitionRangeInput} from './asInput';
import {AssetWipeMutation, AssetWipeMutationVariables} from './types/AssetWipeDialog.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {NavigationBlock} from '../runs/NavigationBlock';
import {Inner, Row} from '../ui/VirtualizedTable';
import {numberFormatter} from '../ui/formatters';

interface AssetKey {
  path: string[];
}

const CHUNK_SIZE = 100;

export const AssetWipeDialog = memo(
  (props: {
    assetKeys: AssetKey[];
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
    assetKeys: AssetKey[];
    onClose: () => void;
    onComplete?: () => void;
    requery?: RefetchQueriesFunction;
  }) => {
    const [requestWipe] = useMutation<AssetWipeMutation, AssetWipeMutationVariables>(
      ASSET_WIPE_MUTATION,
      {
        refetchQueries: requery,
      },
    );

    const [isWiping, setIsWiping] = useState(false);
    const [wipedCount, setWipedCount] = useState(0);
    const [failedCount, setFailedCount] = useState(0);

    const isDone = !isWiping && (wipedCount || failedCount);

    const didCancel = useRef(false);
    const wipe = async () => {
      if (!assetKeys.length) {
        return;
      }
      setIsWiping(true);
      for (let i = 0, l = assetKeys.length; i < l; i += CHUNK_SIZE) {
        if (didCancel.current) {
          return;
        }
        const nextChunk = assetKeys.slice(i, i + CHUNK_SIZE);
        const result = await requestWipe({
          variables: {assetPartitionRanges: nextChunk.map((x) => asAssetPartitionRangeInput(x))},
          refetchQueries: requery,
        });
        const data = result.data?.wipeAssets;
        switch (data?.__typename) {
          case 'AssetNotFoundError':
          case 'PythonError':
            setFailedCount((failed) => failed + nextChunk.length);
            break;
          case 'AssetWipeSuccess':
            setWipedCount((wiped) => wiped + nextChunk.length);
            break;
          case 'UnauthorizedError':
            showCustomAlert({
              title: 'Could not wipe asset materializations',
              body: 'You do not have permission to do this.',
            });
            onClose();
            return;
        }
      }
      onComplete?.();
      setIsWiping(false);
    };

    useLayoutEffect(() => {
      return () => {
        didCancel.current = true;
      };
    }, []);

    const parentRef = useRef<HTMLDivElement>(null);

    const rowVirtualizer = useVirtualizer({
      count: assetKeys.length,
      getScrollElement: () => parentRef.current,
      estimateSize: () => 24,
      overscan: 10,
    });

    const totalHeight = rowVirtualizer.getTotalSize();
    const items = rowVirtualizer.getVirtualItems();

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
            <div style={{maxHeight: '50vh', overflowY: 'scroll'}} ref={parentRef}>
              <Inner $totalHeight={totalHeight}>
                {items.map(({index, key, size, start}) => {
                  const assetKey = assetKeys[index]!;
                  return (
                    <Row key={key} $height={size} $start={start}>
                      {displayNameForAssetKey(assetKey)}
                    </Row>
                  );
                })}
              </Inner>
            </div>
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
    }, [isDone, isWiping, assetKeys, wipedCount, failedCount, totalHeight, items]);

    return (
      <>
        <DialogBody>{content}</DialogBody>
        <DialogFooter topBorder>
          <Button intent={isDone ? 'primary' : 'none'} onClick={onClose}>
            {isDone ? 'Done' : 'Cancel'}
          </Button>
          {isDone ? null : (
            <Button intent="danger" onClick={wipe} disabled={isWiping} loading={isWiping}>
              Wipe
            </Button>
          )}
        </DialogFooter>
      </>
    );
  },
);

const ASSET_WIPE_MUTATION = gql`
  mutation AssetWipeMutation($assetPartitionRanges: [PartitionsByAssetSelector!]!) {
    wipeAssets(assetPartitionRanges: $assetPartitionRanges) {
      ... on AssetWipeSuccess {
        assetPartitionRanges {
          assetKey {
            path
          }
          partitionRange {
            start
            end
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
