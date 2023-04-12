import {gql, useMutation} from '@apollo/client';
import {Group, Table} from '@dagster-io/ui';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SharedToaster} from '../app/DomUtils';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';

import {BackfillPartitionsRequestedDialog} from './BackfillPartitionsRequestedDialog';
import {BackfillRow} from './BackfillRow';
import {BackfillStepStatusDialog} from './BackfillStepStatusDialog';
import {BackfillTerminationDialog} from './BackfillTerminationDialog';
import {RESUME_BACKFILL_MUTATION} from './BackfillUtils';
import {BackfillTableFragment} from './types/BackfillTable.types';
import {ResumeBackfillMutation, ResumeBackfillMutationVariables} from './types/BackfillUtils.types';

export const BackfillTable = ({
  showBackfillTarget = true,
  allPartitions,
  backfills,
  refetch,
}: {
  allPartitions?: string[];
  backfills: BackfillTableFragment[];
  refetch: () => void;
  showBackfillTarget?: boolean;
}) => {
  const [terminationBackfill, setTerminationBackfill] = React.useState<BackfillTableFragment>();
  const [stepStatusBackfill, setStepStatusBackfill] = React.useState<BackfillTableFragment>();
  const [
    partitionsRequestedBackfill,
    setPartitionsRequestedBackfill,
  ] = React.useState<BackfillTableFragment>();
  const [resumeBackfill] = useMutation<ResumeBackfillMutation, ResumeBackfillMutationVariables>(
    RESUME_BACKFILL_MUTATION,
  );

  const candidateId = terminationBackfill?.id;

  React.useEffect(() => {
    if (candidateId) {
      const [backfill] = backfills.filter(
        (backfill) => backfill.id === candidateId && backfill.hasCancelPermission,
      );
      setTerminationBackfill(backfill);
    }
  }, [backfills, candidateId]);

  const resume = async (backfill: BackfillTableFragment) => {
    const {data} = await resumeBackfill({variables: {backfillId: backfill.id}});
    if (data && data.resumePartitionBackfill.__typename === 'ResumeBackfillSuccess') {
      refetch();
    } else if (data && data.resumePartitionBackfill.__typename === 'UnauthorizedError') {
      SharedToaster.show({
        message: (
          <Group direction="column" spacing={4}>
            <div>
              Attempted to retry the backfill in read-only mode. This backfill was not retried.
            </div>
          </Group>
        ),
        icon: 'error',
        intent: 'danger',
      });
    } else if (data && data.resumePartitionBackfill.__typename === 'PythonError') {
      const error = data.resumePartitionBackfill;
      SharedToaster.show({
        message: <div>An unexpected error occurred. This backfill was not retried.</div>,
        icon: 'error',
        intent: 'danger',
        action: {
          text: 'View error',
          onClick: () =>
            showCustomAlert({
              body: <PythonErrorInfo error={error} />,
            }),
        },
      });
    }
  };

  return (
    <>
      <Table>
        <thead>
          <tr>
            <th>Backfill ID</th>
            <th>Created</th>
            {showBackfillTarget ? <th>Backfill target</th> : null}
            <th>Requested</th>
            <th>Backfill status</th>
            <th>Run status</th>
            <th style={{width: 80}} />
          </tr>
        </thead>
        <tbody>
          {backfills.map((backfill) => (
            <BackfillRow
              key={backfill.id}
              showBackfillTarget={showBackfillTarget}
              backfill={backfill}
              allPartitions={allPartitions}
              onTerminateBackfill={setTerminationBackfill}
              onResumeBackfill={resume}
              onShowStepStatus={setStepStatusBackfill}
              onShowPartitionsRequested={setPartitionsRequestedBackfill}
            />
          ))}
        </tbody>
      </Table>
      <BackfillStepStatusDialog
        backfill={stepStatusBackfill}
        onClose={() => setStepStatusBackfill(undefined)}
      />
      <BackfillPartitionsRequestedDialog
        backfill={partitionsRequestedBackfill}
        onClose={() => setPartitionsRequestedBackfill(undefined)}
      />
      <BackfillTerminationDialog
        backfill={terminationBackfill}
        onClose={() => setTerminationBackfill(undefined)}
        onComplete={() => refetch()}
      />
    </>
  );
};

export const BACKFILL_TABLE_FRAGMENT = gql`
  fragment BackfillTableFragment on PartitionBackfill {
    id
    status
    isAssetBackfill
    hasCancelPermission
    hasResumePermission
    numCancelable
    partitionNames
    isValidSerialization
    numPartitions
    timestamp
    partitionSetName
    partitionSet {
      id
      ...PartitionSetForBackfillTable
    }
    assetSelection {
      path
    }
    error {
      ...PythonErrorFragment
    }
  }

  fragment PartitionSetForBackfillTable on PartitionSet {
    id
    name
    mode
    pipelineName
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
