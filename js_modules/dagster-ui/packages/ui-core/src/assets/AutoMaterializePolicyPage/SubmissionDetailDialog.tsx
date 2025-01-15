import {
  Box,
  Dialog,
  HeaderCell,
  Row,
  RowCell,
  Inner
} from '@dagster-io/ui-components';
import {DialogHeader} from './EvaluationDetailDialog';
import { Container, HeaderRow } from 'shared/ui/VirtualizedTable';
import {useVirtualizer} from '@tanstack/react-virtual';
import { useRef } from 'react';
import styled from 'styled-components';

const TEMPLATE_COLUMNS = '50% 50%';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  assetKeyPath: string[];
  assetCheckName?: string;
  requestedPartitionKeys?: string[];
  submittedPartitionKeys?: string[];
}

export const SubmissionDetailDialog = ({
  isOpen,
  onClose,
  assetKeyPath,
  assetCheckName,
  requestedPartitionKeys,
  submittedPartitionKeys,
}: Props) => {
  console.log(requestedPartitionKeys);
  console.log(submittedPartitionKeys);
  const parentRef = useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: requestedPartitionKeys?.length || 0,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();
  return (
    <Dialog isOpen={isOpen} onClose={onClose} style={EvaluationDetailDialogStyle}>
      <DialogHeader assetKeyPath={assetKeyPath} assetCheckName={assetCheckName} />
      <Container ref={parentRef}>
        <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
          <HeaderCell>Partition</HeaderCell>
          <HeaderCell>Submitted</HeaderCell>
        </HeaderRow>
        <Inner $totalHeight={totalHeight}>
          {items?.map(({index, key, size, start}) => {
            const partitionKey = requestedPartitionKeys?.[index];
            const returnVal = partitionKey ? (
              <Row $height={size} $start={start} key={key}>
                <RowGrid border="bottom">
                  <RowCell>{partitionKey}</RowCell>
                  <RowCell>
                    {submittedPartitionKeys?.includes(partitionKey) ? 'True' : 'False'}
                  </RowCell>
                </RowGrid>
              </Row>
            ) : null;
            return returnVal;
          })}
        </Inner>
      </Container>
    </Dialog>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
  > * {
    justify-content: center;
  }
`;

const EvaluationDetailDialogStyle = {
  width: '80vw',
  maxWidth: '1400px',
  minWidth: '800px',
  height: '80vh',
  minHeight: '400px',
  maxHeight: '1400px',
};
