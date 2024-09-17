import {Button, Dialog, DialogFooter} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {BackfillStepStatusDialogBackfillFragment} from './types/BackfillFragments.types';
import {PartitionPerOpStatus} from '../../partitions/PartitionStepStatus';
import {usePartitionStepQuery} from '../../partitions/usePartitionStepQuery';
import {DagsterTag} from '../../runs/RunTag';
import {RunFilterToken} from '../../runs/RunsFilterInput';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {repoAddressToSelector} from '../../workspace/repoAddressToSelector';
import {RepoAddress} from '../../workspace/types';

interface Props {
  backfill?: BackfillStepStatusDialogBackfillFragment;
  onClose: () => void;
}

export function backfillCanShowStepStatus(
  backfill?: BackfillStepStatusDialogBackfillFragment,
): backfill is BackfillStepStatusDialogBackfillFragment & {
  partitionSet: NonNullable<BackfillStepStatusDialogBackfillFragment['partitionSet']>;
  partitionNames: string[];
} {
  return !!backfill && backfill.partitionSet !== null && backfill.partitionNames !== null;
}

export const BackfillStepStatusDialog = ({backfill, onClose}: Props) => {
  const content = () => {
    if (!backfillCanShowStepStatus(backfill)) {
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
        partitionNames={backfill.partitionNames}
        repoAddress={repoAddress}
        onClose={onClose}
      />
    );
  };

  return (
    <Dialog
      isOpen={!!backfill?.partitionSet}
      title={`Step status for backfill: ${backfill?.id}`}
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
  backfill: BackfillStepStatusDialogBackfillFragment;
  partitionSet: NonNullable<BackfillStepStatusDialogBackfillFragment['partitionSet']>;
  partitionNames: string[];
  repoAddress: RepoAddress;
  onClose: () => void;
}

const BackfillStepStatusDialogContent = ({
  backfill,
  partitionSet,
  partitionNames,
  repoAddress,
}: ContentProps) => {
  const [pageSize, setPageSize] = useState(60);
  const [offset, setOffset] = useState<number>(0);

  const runsFilter = useMemo(() => {
    const token: RunFilterToken = {token: 'tag', value: `dagster/backfill=${backfill.id}`};
    return [token];
  }, [backfill.id]);

  const partitions = usePartitionStepQuery({
    partitionSetName: partitionSet.name,
    partitionTagName: DagsterTag.Partition,
    partitionNames,
    pageSize,
    runsFilter,
    repositorySelector: repoAddressToSelector(repoAddress),
    jobName: partitionSet.pipelineName,
    offset,
    skipQuery: !backfill,
  });

  return (
    <PartitionPerOpStatus
      partitionNames={partitionNames}
      partitions={partitions}
      pipelineName={partitionSet?.pipelineName}
      repoAddress={repoAddress}
      setPageSize={setPageSize}
      offset={offset}
      setOffset={setOffset}
    />
  );
};
