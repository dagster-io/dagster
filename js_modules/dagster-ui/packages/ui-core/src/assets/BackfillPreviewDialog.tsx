import {Box, Button, Colors, Dialog, DialogFooter, Spinner} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useMemo, useRef} from 'react';
import styled from 'styled-components';

import {AssetLink} from './AssetLink';
import {asAssetKeyInput} from './asInput';
import {AssetKey} from './types';
import {gql, useQuery} from '../apollo-client';
import {
  BackfillPreviewQuery,
  BackfillPreviewQueryVariables,
} from './types/BackfillPreviewDialog.types';
import {
  BackfillPolicyForLaunchAssetFragment,
  PartitionDefinitionForLaunchAssetFragment,
} from './types/LaunchAssetExecutionButton.types';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {TargetPartitionsDisplay} from '../instance/backfill/TargetPartitionsDisplay';
import {testId} from '../testing/testId';
import {Container, HeaderCell, HeaderRow, Inner, Row, RowCell} from '../ui/VirtualizedTable';

interface BackfillPreviewDialogProps {
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

export const BackfillPreviewDialog = ({
  isOpen,
  setOpen,
  assets,
  keysFiltered,
}: BackfillPreviewDialogProps) => {
  const assetKeys = useMemo(() => assets.map(asAssetKeyInput), [assets]);
  const parentRef = useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: assets.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  const queryResult = useQuery<BackfillPreviewQuery, BackfillPreviewQueryVariables>(
    BACKFILL_PREVIEW_QUERY,
    {
      variables: {partitionNames: keysFiltered, assetKeys},
      skip: !isOpen,
    },
  );
  const {data, loading} = queryResult;

  const partitionsByAssetToken = useMemo(() => {
    return Object.fromEntries(
      (data?.assetBackfillPreview || []).map((d) => [tokenForAssetKey(d.assetKey), d.partitions]),
    );
  }, [data]);

  return (
    <Dialog
      title="Backfill preview"
      isOpen={isOpen}
      onClose={() => setOpen(false)}
      style={{width: '90vw', maxWidth: 1100}}
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
                    ) : loading ? (
                      <Spinner purpose="body-text" />
                    ) : (
                      'No partitions available to materialize'
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
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>Asset key</HeaderCell>
      <HeaderCell>Backfill policy</HeaderCell>
      <HeaderCell>Partition definition</HeaderCell>
      <HeaderCell>Partitions to launch</HeaderCell>
    </HeaderRow>
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
