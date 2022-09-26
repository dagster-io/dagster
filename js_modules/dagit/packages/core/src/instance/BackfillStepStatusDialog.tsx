import {Button, DialogFooter, Dialog} from '@dagster-io/ui';
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
  const content = () => {
    if (!backfill?.partitionSet) {
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

  return (
    <Dialog
      isOpen={!!backfill?.partitionSet}
      title={`Step status for backfill: ${backfill?.backfillId}`}
      onClose={onClose}
      style={{width: '80vw'}}
    >
      {content()}
      <DialogFooter topBorder>
        <Button onClick={onClose}>Done</Button>
      </DialogFooter>
    </Dialog>
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

  return (
    <PartitionStepStatus
      partitionNames={backfill.partitionNames}
      partitions={partitions}
      pipelineName={partitionSet?.pipelineName}
      repoAddress={repoAddress}
      setPageSize={setPageSize}
      offset={offset}
      setOffset={setOffset}
    />
  );
};
