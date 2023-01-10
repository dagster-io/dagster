import {useMutation} from '@apollo/client';
import {Group, Table} from '@dagster-io/ui';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SharedToaster} from '../app/DomUtils';
import {usePermissionsDEPRECATED} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {graphql} from '../graphql';
import {BackfillTableFragmentFragment} from '../graphql/graphql';

import {BackfillPartitionsRequestedDialog} from './BackfillPartitionsRequestedDialog';
import {BackfillRow} from './BackfillRow';
import {BackfillStepStatusDialog} from './BackfillStepStatusDialog';
import {BackfillTerminationDialog} from './BackfillTerminationDialog';
import {RESUME_BACKFILL_MUTATION} from './BackfillUtils';

export const BackfillTable = ({
  showBackfillTarget = true,
  allPartitions,
  backfills,
  refetch,
}: {
  allPartitions?: string[];
  backfills: BackfillTableFragmentFragment[];
  refetch: () => void;
  showBackfillTarget?: boolean;
}) => {
  const [
    terminationBackfill,
    setTerminationBackfill,
  ] = React.useState<BackfillTableFragmentFragment>();
  const [
    stepStatusBackfill,
    setStepStatusBackfill,
  ] = React.useState<BackfillTableFragmentFragment>();
  const [
    partitionsRequestedBackfill,
    setPartitionsRequestedBackfill,
  ] = React.useState<BackfillTableFragmentFragment>();
  const [resumeBackfill] = useMutation(RESUME_BACKFILL_MUTATION);
  const {canCancelPartitionBackfill} = usePermissionsDEPRECATED();

  const candidateId = terminationBackfill?.backfillId;

  React.useEffect(() => {
    if (canCancelPartitionBackfill.enabled && candidateId) {
      const [backfill] = backfills.filter((backfill) => backfill.backfillId === candidateId);
      setTerminationBackfill(backfill);
    }
  }, [backfills, candidateId, canCancelPartitionBackfill]);

  const resume = async (backfill: BackfillTableFragmentFragment) => {
    const {data} = await resumeBackfill({variables: {backfillId: backfill.backfillId}});
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
      <Table $monospaceFont={false}>
        <thead>
          <tr>
            <th style={{width: 120}}>Backfill ID</th>
            <th style={{width: 200}}>Created</th>
            {showBackfillTarget ? <th>Backfill target</th> : null}
            {allPartitions ? <th>Requested</th> : null}
            <th style={{width: 140}}>Backfill status</th>
            <th>Run status</th>
            <th style={{width: 80}} />
          </tr>
        </thead>
        <tbody>
          {backfills.map((backfill) => (
            <BackfillRow
              key={backfill.backfillId}
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

export const BACKFILL_TABLE_FRAGMENT = graphql(`
  fragment BackfillTableFragment on PartitionBackfill {
    backfillId
    status
    numCancelable
    partitionNames
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
`);
