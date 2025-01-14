import {
  Box,
  Dialog,
  HeaderCell,
  Row,
  RowCell
} from '@dagster-io/ui-components';
import {DialogHeader} from './EvaluationDetailDialog';
import { HeaderRow } from 'shared/ui/VirtualizedTable';
import { TEMPLATE_COLUMNS } from 'shared/automation/VirtualizedAutomationRow';

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
  return (
    <Dialog isOpen={isOpen} onClose={onClose} style={EvaluationDetailDialogStyle}>
       <div>
        <DialogHeader assetKeyPath={assetKeyPath} assetCheckName={assetCheckName} />
        <div style={{flex: 1, overflowY: 'auto'}}>
          <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
            <HeaderCell>Partition</HeaderCell>
            <HeaderCell>Submitted</HeaderCell>
          </HeaderRow>
        </div>
        <div>
          {requestedPartitionKeys?.map((partitionKey) => {
            return (
              <Row $height={10} $start={10} key={partitionKey}>
                <RowCell>partitionKey</RowCell>
                <RowCell>{submittedPartitionKeys?.includes(partitionKey) ? 'True' : 'False'}</RowCell>
              </Row>
            );
          })}
        </div>
      </div>
    </Dialog>
  );
};

const EvaluationDetailDialogStyle = {
  width: '80vw',
  maxWidth: '1400px',
  minWidth: '800px',
  height: '80vh',
  minHeight: '400px',
  maxHeight: '1400px',
};
