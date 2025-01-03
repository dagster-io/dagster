import {
  Box,
  Button,
  Dialog,
  DialogFooter,
  DialogHeader,
  Mono,
  NonIdealState,
  SpinnerWithText,
} from '@dagster-io/ui-components';
import {ReactNode, useState} from 'react';

import {GET_SLIM_EVALUATIONS_QUERY} from './GetEvaluationsQuery';
import {PartitionTagSelector} from './PartitionTagSelector';
import {QueryfulEvaluationDetailTable} from './QueryfulEvaluationDetailTable';
import {
  GetSlimEvaluationsQuery,
  GetSlimEvaluationsQueryVariables,
} from './types/GetEvaluationsQuery.types';
import {usePartitionsForAssetKey} from './usePartitionsForAssetKey';
import {useQuery} from '../../apollo-client';
import {DEFAULT_TIME_FORMAT} from '../../app/time/TimestampFormat';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  assetKeyPath: string[];
  assetCheckName?: string;
  evaluationID: string;
}

export const EvaluationDetailDialog = ({
  isOpen,
  onClose,
  evaluationID,
  assetKeyPath,
  assetCheckName,
}: Props) => {
  return (
    <Dialog isOpen={isOpen} onClose={onClose} style={EvaluationDetailDialogStyle}>
      <EvaluationDetailDialogContents
        evaluationID={evaluationID}
        assetKeyPath={assetKeyPath}
        assetCheckName={assetCheckName}
        onClose={onClose}
      />
    </Dialog>
  );
};

interface ContentProps {
  evaluationID: string;
  assetKeyPath: string[];
  assetCheckName?: string;
  onClose: () => void;
}

const EvaluationDetailDialogContents = ({
  evaluationID,
  assetKeyPath,
  assetCheckName,
  onClose,
}: ContentProps) => {
  const [selectedPartition, setSelectedPartition] = useState<string | null>(null);

  const {data, loading} = useQuery<GetSlimEvaluationsQuery, GetSlimEvaluationsQueryVariables>(
    GET_SLIM_EVALUATIONS_QUERY,
    {
      variables: {
        assetKey: assetCheckName ? null : {path: assetKeyPath},
        assetCheckKey: assetCheckName
          ? {assetKey: {path: assetKeyPath}, name: assetCheckName}
          : null,
        cursor: `${BigInt(evaluationID) + 1n}`,
        limit: 2,
      },
    },
  );

  const {partitions: allPartitions, loading: partitionsLoading} =
    usePartitionsForAssetKey(assetKeyPath);

  if (loading || partitionsLoading) {
    return (
      <DialogContents
        header={<DialogHeader icon="automation" label="Evaluation details" />}
        body={
          <Box padding={{top: 64}} flex={{direction: 'row', justifyContent: 'center'}}>
            <SpinnerWithText label="Loading evaluation details..." />
          </Box>
        }
        onDone={onClose}
      />
    );
  }

  const record = data?.assetConditionEvaluationRecordsOrError;

  if (record?.__typename === 'AutoMaterializeAssetEvaluationNeedsMigrationError') {
    return (
      <DialogContents
        header={<DialogHeader icon="automation" label="Evaluation details" />}
        body={
          <Box margin={{top: 64}}>
            <NonIdealState
              icon="automation"
              title="Evaluation needs migration"
              description={record.message}
            />
          </Box>
        }
        onDone={onClose}
      />
    );
  }

  const evaluation = record?.records.find((r) => r.evaluationId === evaluationID);

  if (!evaluation) {
    return (
      <DialogContents
        header={<DialogHeader icon="automation" label="Evaluation details" />}
        body={
          <Box margin={{top: 64}}>
            <NonIdealState
              icon="automation"
              title="Evaluation not found"
              description={
                <>
                  Evaluation <Mono>{evaluationID}</Mono> not found
                </>
              }
            />
          </Box>
        }
        onDone={onClose}
      />
    );
  }

  return (
    <DialogContents
      header={
        <>
          <DialogHeader
            icon="automation"
            label={
              <div>
                Evaluation details:{' '}
                <TimestampDisplay
                  timestamp={evaluation.timestamp}
                  timeFormat={{...DEFAULT_TIME_FORMAT, showSeconds: true}}
                />
              </div>
            }
          />
          {allPartitions.length > 0 && evaluation.isLegacy ? (
            <Box padding={{vertical: 12, right: 20}} flex={{justifyContent: 'flex-end'}}>
              <PartitionTagSelector
                allPartitions={allPartitions}
                selectedPartition={selectedPartition}
                selectPartition={setSelectedPartition}
              />
            </Box>
          ) : null}
        </>
      }
      body={
        <QueryfulEvaluationDetailTable
          evaluation={evaluation}
          assetKeyPath={assetKeyPath}
          selectedPartition={selectedPartition}
          setSelectedPartition={setSelectedPartition}
        />
      }
      onDone={onClose}
    />
  );
};

interface BasicContentProps {
  header: ReactNode;
  body: ReactNode;
  onDone: () => void;
}

// Dialog contents for which the body container is scrollable and expands to fill the height.
const DialogContents = ({header, body, onDone}: BasicContentProps) => {
  return (
    <Box flex={{direction: 'column'}} style={{height: '100%'}}>
      {header}
      <div style={{flex: 1, overflowY: 'auto'}}>{body}</div>
      <div style={{flexGrow: 0}}>
        <DialogFooter topBorder>
          <Button onClick={onDone}>Done</Button>
        </DialogFooter>
      </div>
    </Box>
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
