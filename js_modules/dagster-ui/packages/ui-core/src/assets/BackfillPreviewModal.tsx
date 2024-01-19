import {gql, useQuery} from '@apollo/client';
import {Box, Button, Dialog, DialogFooter, Spinner, Colors} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import styled from 'styled-components';

import {tokenForAssetKey} from '../asset-graph/Utils';
import {TargetPartitionsDisplay} from '../instance/backfill/TargetPartitionsDisplay';
import {testId} from '../testing/testId';
import {Container, HeaderCell, Inner, Row, RowCell} from '../ui/VirtualizedTable';

import {AssetLink} from './AssetLink';
import {asAssetKeyInput} from './asInput';
import {AssetKey} from './types';
import {
  BackfillPreviewQuery,
  BackfillPreviewQueryVariables,
} from './types/BackfillPreviewModal.types';
import {
  BackfillPolicyForLaunchAssetFragment,
  PartitionDefinitionForLaunchAssetFragment,
} from './types/LaunchAssetExecutionButton.types';

interface BackfillPreviewModalProps {
  isOpen: boolean;
  assets: {
    assetKey: AssetKey;
    partitionDefinition: PartitionDefinitionForLaunchAssetFragment | null;
    backfillPolicy: BackfillPolicyForLaunchAssetFragment | null;
  }[];
  keysFiltered: string[];
  setOpen: (isOpen: boolean) => void;
}
const TEMPLATE_COLUMNS = '1fr 1fr 1fr 1fr';

export const BackfillPreviewModal = ({
  isOpen,
  setOpen,
  assets,
  keysFiltered,
}: BackfillPreviewModalProps) => {
  const assetKeys = React.useMemo(() => assets.map(asAssetKeyInput), [assets]);
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: assets.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  const {data} = useQuery<BackfillPreviewQuery, BackfillPreviewQueryVariables>(
    BACKFILL_PREVIEW_QUERY,
    {
      variables: {partitionNames: keysFiltered, assetKeys},
      skip: !isOpen,
    },
  );

  const partitionsByAssetToken = React.useMemo(() => {
    return Object.fromEntries(
      (data?.assetBackfillPreview || []).map((d) => [tokenForAssetKey(d.assetKey), d.partitions]),
    );
  }, [data]);

  // BG Note: The transform: scale(1) below fixes a bug with MiddleTruncate where the text size
  // is measured while the dialog is animating open and the scale is < 1, causing it to think
  // it needs to truncate. A more general fix for this seems like it'll require a lot of testing.

  return (
    <Dialog
      title="Backfill preview"
      isOpen={isOpen}
      onClose={() => setOpen(false)}
      style={{width: '90vw', maxWidth: 1100, transform: 'scale(1)'}}
    >
      <Container
        ref={parentRef}
        style={{maxHeight: '50vh'}}
        data-testid={testId('backfill-preview-modal-content')}
      >
        <BackfillPreviewTableHeader />
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, size, start}) => {
            const {assetKey, partitionDefinition, backfillPolicy} = assets[index]!;
            const token = tokenForAssetKey(assetKey);
            const partitions = partitionsByAssetToken[token];

            return (
              <Row key={token} $height={size} $start={start}>
                <RowGrid border={index < assets.length - 1 ? 'bottom' : undefined}>
                  <RowCell>
                    <AssetLink path={assetKey.path} textStyle="middle-truncate" icon="asset" />
                  </RowCell>
                  {backfillPolicy ? (
                    <RowCell style={{color: Colors.textDefault()}}>
                      {backfillPolicy?.description}
                    </RowCell>
                  ) : (
                    <RowCell>{'\u2013'}</RowCell>
                  )}
                  {partitionDefinition ? (
                    <RowCell style={{color: Colors.textDefault()}}>
                      {partitionDefinition?.description}
                    </RowCell>
                  ) : (
                    <RowCell>{'\u2013'}</RowCell>
                  )}
                  <RowCell style={{color: Colors.textDefault(), alignItems: 'flex-start'}}>
                    {partitions ? (
                      <TargetPartitionsDisplay targetPartitions={partitions} />
                    ) : (
                      <Spinner purpose="body-text" />
                    )}
                  </RowCell>
                </RowGrid>
              </Row>
            );
          })}
        </Inner>
      </Container>
      <DialogFooter topBorder>
        <Button intent="primary" autoFocus={true} onClick={() => setOpen(false)}>
          OK
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
`;

export const BackfillPreviewTableHeader = () => {
  return (
    <Box
      border="bottom"
      style={{
        display: 'grid',
        gridTemplateColumns: TEMPLATE_COLUMNS,
        height: '32px',
        fontSize: '12px',
        color: Colors.textLight(),
      }}
    >
      <HeaderCell>Asset key</HeaderCell>
      <HeaderCell>Backfill policy</HeaderCell>
      <HeaderCell>Partition definition</HeaderCell>
      <HeaderCell>Partitions to launch</HeaderCell>
    </Box>
  );
};

export const BACKFILL_PREVIEW_QUERY = gql`
  query BackfillPreviewQuery($partitionNames: [String!]!, $assetKeys: [AssetKeyInput!]!) {
    assetBackfillPreview(params: {partitionNames: $partitionNames, assetSelection: $assetKeys}) {
      assetKey {
        path
      }
      partitions {
        partitionKeys
        ranges {
          start
          end
        }
      }
    }
  }
`;
