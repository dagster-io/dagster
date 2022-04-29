import {Button, DialogBody, DialogFooter, Dialog} from '@dagster-io/ui';
import * as React from 'react';

import {PartitionStepStatus} from '../partitions/PartitionStepStatus';
import {usePartitionStepQuery} from '../partitions/usePartitionStepQuery';
import {RunFilterToken} from '../runs/RunsFilterInput';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';

import {
  BackfillTableFragment,
  BackfillTableFragment_partitionSet,
} from './types/BackfillTableFragment';

interface Props {
  backfill?: BackfillTableFragment;
  onClose: () => void;
}
export const BackfillStepStatusDialog = ({backfill, onClose}: Props) => {
  if (!backfill) {
    return null;
  }
  if (!backfill.partitionSet) {
    return null;
  }
  const repoAddress = buildRepoAddress(
    backfill.partitionSet.repositoryOrigin.repositoryName,
    backfill.partitionSet.repositoryOrigin.repositoryLocationName,
  );
  return (
    <BackfillStepStatusDialogContent
      backfill={backfill}
      partitionSet={backfill.partitionSet}
      repoAddress={repoAddress}
      onClose={onClose}
    />
  );
};

interface ContentProps {
  backfill: BackfillTableFragment;
  partitionSet: BackfillTableFragment_partitionSet;
  repoAddress: RepoAddress;
  onClose: () => void;
}

export const BackfillStepStatusDialogContent = ({
  backfill,
  partitionSet,
  repoAddress,
  onClose,
}: ContentProps) => {
  const [pageSize, setPageSize] = React.useState(60);
  const [offset, setOffset] = React.useState<number>(0);
  const runsFilter = React.useMemo(() => {
    const token: RunFilterToken = {token: 'tag', value: `dagster/backfill=${backfill.backfillId}`};
    return [token];
  }, [backfill.backfillId]);
  const partitions = usePartitionStepQuery(
    partitionSet.name,
    backfill.partitionNames,
    pageSize,
    runsFilter,
    partitionSet.pipelineName,
    offset,
    !backfill,
  );

  if (!backfill) {
    return null;
  }

  return (
    <Dialog
      isOpen={!!backfill}
      title={
        <span>
          Step status for backfill:{' '}
          <span style={{fontFamily: 'monospace'}}>{backfill.backfillId}</span>
        </span>
      }
      onClose={onClose}
      style={{width: '80vw'}}
    >
      <DialogBody>
        <PartitionStepStatus
          partitionNames={backfill.partitionNames}
          partitions={partitions}
          pipelineName={partitionSet?.pipelineName}
          repoAddress={repoAddress}
          setPageSize={setPageSize}
          offset={offset}
          setOffset={setOffset}
        />
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onClose}>
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
