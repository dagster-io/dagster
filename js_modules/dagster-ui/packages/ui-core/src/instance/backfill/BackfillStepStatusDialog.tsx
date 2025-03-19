import {Box, Button, Dialog, DialogFooter, SpinnerWithText} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {BackfillTableFragmentForStepStatusDialogFragment} from './types/BackfillFragments.types';
import {
  BackfillStepStatusDialogBackfillFragment,
  BackfillStepStatusDialogContentQuery,
  BackfillStepStatusDialogContentQueryVariables,
} from './types/BackfillStepStatusDialog.types';
import {gql, useQuery} from '../../apollo-client';
import {PartitionPerOpStatus} from '../../partitions/PartitionStepStatus';
import {usePartitionStepQuery} from '../../partitions/usePartitionStepQuery';
import {DagsterTag} from '../../runs/RunTag';
import {RunFilterToken} from '../../runs/RunsFilterInput';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {repoAddressToSelector} from '../../workspace/repoAddressToSelector';
import {RepoAddress} from '../../workspace/types';

interface Props {
  backfill?: BackfillTableFragmentForStepStatusDialogFragment;
  onClose: () => void;
}

export function backfillCanShowStepStatus(
  backfill?: BackfillTableFragmentForStepStatusDialogFragment,
) {
  return !!backfill && backfill.partitionSet !== null;
}

export const BackfillStepStatusDialog = ({backfill, onClose}: Props) => {
  const content = () => {
    if (!backfillCanShowStepStatus(backfill)) {
      return null;
    }

    return (
      <BackfillStepStatusDialogContentNameLoader backfillId={backfill!.id} onClose={onClose} />
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

const BackfillStepStatusDialogContentNameLoader = ({
  backfillId,
  onClose,
}: {
  backfillId: string;
  onClose: () => void;
}) => {
  const queryResult = useQuery<
    BackfillStepStatusDialogContentQuery,
    BackfillStepStatusDialogContentQueryVariables
  >(BACKFILL_STEP_STATUS_DIALOG_CONTENT_QUERY, {
    skip: !backfillId,
    variables: {backfillId},
  });

  const {data, loading} = queryResult;
  if (loading) {
    return (
      <Box style={{padding: 64}} flex={{alignItems: 'center', justifyContent: 'center'}}>
        <SpinnerWithText label="Loading partitions…" />
      </Box>
    );
  }

  const backfill = data?.partitionBackfillOrError;
  if (
    !backfill ||
    backfill.__typename !== 'PartitionBackfill' ||
    !backfill.partitionSet ||
    !backfill.partitionNames
  ) {
    // TODO: handle error
    return (
      <Box style={{padding: 64}} flex={{alignItems: 'center', justifyContent: 'center'}}>
        <SpinnerWithText label="Loading partitions…" />
      </Box>
    );
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

const BACKFILL_STEP_STATUS_DIALOG_CONTENT_QUERY = gql`
  query BackfillStepStatusDialogContentQuery($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        id
        partitionNames
        ...BackfillStepStatusDialogBackfillFragment
      }
    }
  }

  fragment BackfillStepStatusDialogBackfillFragment on PartitionBackfill {
    id
    partitionNames
    partitionSet {
      id
      mode
      name
      pipelineName
      repositoryOrigin {
        id
        repositoryName
        repositoryLocationName
      }
    }
  }
`;
