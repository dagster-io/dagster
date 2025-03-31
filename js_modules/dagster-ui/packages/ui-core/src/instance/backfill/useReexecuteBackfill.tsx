import {Group} from '@dagster-io/ui-components';

import {gql, useMutation} from '../../apollo-client';
import {BackfillActionsBackfillFragment} from './types/BackfillFragments.types';
import {
  ReexecuteBackfillMutation,
  ReexecuteBackfillMutationVariables,
} from './types/useReexecuteBackfill.types';
import {showCustomAlert} from '../../app/CustomAlertProvider';
import {showSharedToaster} from '../../app/DomUtils';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {ReexecutionStrategy} from '../../graphql/types';
import {showBackfillSuccessToast} from '../../partitions/BackfillMessaging';

export function useReexecuteBackfill(
  backfill: BackfillActionsBackfillFragment,
  refetch: () => void,
) {
  const [reexecuteBackfill] = useMutation<
    ReexecuteBackfillMutation,
    ReexecuteBackfillMutationVariables
  >(REEXECUTE_BACKFILL_MUTATION);

  return async (strategy: ReexecutionStrategy) => {
    const {data} = await reexecuteBackfill({
      variables: {reexecutionParams: {parentRunId: backfill.id, strategy}},
    });
    if (data && data.reexecutePartitionBackfill.__typename === 'LaunchBackfillSuccess') {
      showBackfillSuccessToast(data.reexecutePartitionBackfill.backfillId, true);
      refetch();
    } else if (data && data.reexecutePartitionBackfill.__typename === 'UnauthorizedError') {
      await showSharedToaster({
        message: (
          <Group direction="column" spacing={4}>
            <div>
              Attempted to re-execute the backfill in read-only mode. This backfill was not
              launched.
            </div>
          </Group>
        ),
        icon: 'error',
        intent: 'danger',
      });
    } else if (data && data.reexecutePartitionBackfill.__typename === 'PythonError') {
      const error = data.reexecutePartitionBackfill;
      await showSharedToaster({
        message: <div>An unexpected error occurred. This backfill was not re-executed.</div>,
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

export const REEXECUTE_BACKFILL_MUTATION = gql`
  mutation reexecuteBackfill($reexecutionParams: ReexecutionParams!) {
    reexecutePartitionBackfill(reexecutionParams: $reexecutionParams) {
      ... on LaunchBackfillSuccess {
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
