import {useCallback, useState} from 'react';
import {useHistory} from 'react-router-dom';

import {LAUNCH_PIPELINE_REEXECUTION_MUTATION, handleLaunchResult} from './RunUtils';
import {gql, useApolloClient, useMutation} from '../apollo-client';
import {ReexecutionDialog, ReexecutionDialogProps} from './ReexecutionDialog';
import {DagsterTag} from './RunTag';
import {useConfirmation} from '../app/CustomConfirmationProvider';
import {
  LaunchPipelineReexecutionMutation,
  LaunchPipelineReexecutionMutationVariables,
} from './types/RunUtils.types';
import {BulkActionStatus, ExecutionParams, ReexecutionStrategy} from '../graphql/types';
import {showLaunchError} from '../launchpad/showLaunchError';
import {
  CheckBackfillStatusQuery,
  CheckBackfillStatusQueryVariables,
} from './types/useJobReExecution.types';

/**
 * This hook gives you a mutation method that you can use to re-execute runs.
 *
 * The preferred way to re-execute runs is to pass a ReexecutionStrategy.
 * If you need to re-execute with more complex parameters, (eg: a custom subset
 * of the previous run), build the variables using `getReexecutionVariables` and
 * pass them to this hook.
 */
export const useJobReexecution = (opts?: {onCompleted?: () => void}) => {
  const history = useHistory();
  const confirm = useConfirmation();
  const client = useApolloClient();
  const {onCompleted} = opts || {};

  const [launchPipelineReexecution] = useMutation<
    LaunchPipelineReexecutionMutation,
    LaunchPipelineReexecutionMutationVariables
  >(LAUNCH_PIPELINE_REEXECUTION_MUTATION);

  const [dialogProps, setDialogProps] = useState<ReexecutionDialogProps | null>(null);
  const onClick = useCallback(
    async (
      run: {id: string; pipelineName: string; tags: {key: string; value: string}[]},
      param: ReexecutionStrategy | ExecutionParams,
      forceLaunchpad: boolean,
    ) => {
      const backfillTag = run.tags.find((t) => t.key === DagsterTag.Backfill);

      if (forceLaunchpad && typeof param === 'string') {
        setDialogProps({
          isOpen: true,
          onClose: () => setDialogProps(null),
          onComplete: () => onCompleted?.(),
          selectedRuns: {[run.id]: run.id},
          selectedRunBackfillIds: backfillTag ? [backfillTag.value] : [],
          reexecutionStrategy: param,
        });
        return;
      }

      if (backfillTag) {
        const {data} = await client.query<
          CheckBackfillStatusQuery,
          CheckBackfillStatusQueryVariables
        >({
          query: CHECK_BACKFILL_STATUS_QUERY,
          fetchPolicy: 'no-cache',
          variables: {
            backfillId: backfillTag.value,
          },
        });
        const backfillRunning =
          data.partitionBackfillOrError.__typename === 'PartitionBackfill'
            ? data.partitionBackfillOrError.status === BulkActionStatus.REQUESTED
            : false;

        if (!backfillRunning) {
          try {
            await confirm({
              title: 'Re-execution within backfill',
              description: `This run is part of a completed backfill. Re-executing will not update the backfill status or launch runs of downstream dependencies.`,
              intent: 'primary',
              catchOnCancel: true,
            });
          } catch {
            return;
          }
        }
      }

      try {
        const result = await launchPipelineReexecution({
          variables:
            typeof param === 'string'
              ? {reexecutionParams: {parentRunId: run.id, strategy: param}}
              : {executionParams: param},
        });
        handleLaunchResult(run.pipelineName, result.data?.launchPipelineReexecution, history, {
          preserveQuerystring: true,
          behavior: 'open',
        });
        onCompleted?.();
      } catch (error) {
        showLaunchError(error as Error);
      }
    },
    [client, confirm, launchPipelineReexecution, history, onCompleted],
  );

  return {
    onClick,
    launchpadElement: dialogProps ? <ReexecutionDialog {...dialogProps} /> : null,
  };
};

const CHECK_BACKFILL_STATUS_QUERY = gql`
  query CheckBackfillStatus($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        id
        status
      }
    }
  }
`;
