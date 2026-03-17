import {Box, showToast} from '@dagster-io/ui-components';

import {gql, useMutation} from '../../apollo-client';
import {BackfillActionsBackfillFragment} from './types/BackfillFragments.types';
import {
  ResumeBackfillMutation,
  ResumeBackfillMutationVariables,
} from './types/useResumeBackfill.types';
import {showCustomAlert} from '../../app/CustomAlertProvider';
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
      showToast({
        message: (
          <Box flex={{direction: 'column', gap: 4}}>
            <div>
              Attempted to resume the backfill in read-only mode. This backfill was not resumed.
            </div>
          </Box>
        ),
        icon: 'error',
        intent: 'danger',
      });
    } else if (data && data.resumePartitionBackfill.__typename === 'PythonError') {
      const error = data.resumePartitionBackfill;
      showToast({
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
