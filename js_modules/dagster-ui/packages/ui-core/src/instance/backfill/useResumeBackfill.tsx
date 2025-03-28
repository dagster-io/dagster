import {Group} from '@dagster-io/ui-components';

import {gql, useMutation} from '../../apollo-client';
import {BackfillActionsBackfillFragment} from './types/BackfillFragments.types';
import {
  ResumeBackfillMutation,
  ResumeBackfillMutationVariables,
} from './types/useResumeBackfill.types';
import {showCustomAlert} from '../../app/CustomAlertProvider';
import {showSharedToaster} from '../../app/DomUtils';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';

export function useResumeBackfill(backfill: BackfillActionsBackfillFragment, refetch: () => void) {
  const [resumeBackfill] = useMutation<ResumeBackfillMutation, ResumeBackfillMutationVariables>(
    RESUME_BACKFILL_MUTATION,
  );

  return async () => {
    const {data} = await resumeBackfill({variables: {backfillId: backfill.id}});
    if (data && data.resumePartitionBackfill.__typename === 'ResumeBackfillSuccess') {
      refetch();
    } else if (data && data.resumePartitionBackfill.__typename === 'UnauthorizedError') {
      await showSharedToaster({
        message: (
          <Group direction="column" spacing={4}>
            <div>
              Attempted to resume the backfill in read-only mode. This backfill was not resumed.
            </div>
          </Group>
        ),
        icon: 'error',
        intent: 'danger',
      });
    } else if (data && data.resumePartitionBackfill.__typename === 'PythonError') {
      const error = data.resumePartitionBackfill;
      await showSharedToaster({
        message: <div>An unexpected error occurred. This backfill was not resumed.</div>,
        icon: 'error',
        intent: 'danger',
        action: {
          type: 'button',
          text: 'View error',
          onClick: () =>
            showCustomAlert({
              body: <PythonErrorInfo error={error} />,
            }),
        },
      });
    }
  };
}

export const RESUME_BACKFILL_MUTATION = gql`
  mutation resumeBackfill($backfillId: String!) {
    resumePartitionBackfill(backfillId: $backfillId) {
      ... on ResumeBackfillSuccess {
        backfillId
      }
      ... on UnauthorizedError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
