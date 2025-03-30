import {MockedProvider} from '@apollo/client/testing';
import {Body, Box, Button, Dialog, DialogBody, DialogFooter} from '@dagster-io/ui-components';
import {renderHook, waitFor} from '@testing-library/react';
import {ReactNode, useCallback, useState} from 'react';
import {useHistory} from 'react-router-dom';

import {LAUNCH_PIPELINE_REEXECUTION_MUTATION, handleLaunchResult} from './RunUtils';
import {gql, useApolloClient, useMutation} from '../apollo-client';
import {DagsterTag} from './RunTag';
import {useConfirmation} from '../app/CustomConfirmationProvider';
import {
  LaunchPipelineReexecutionMutation,
  LaunchPipelineReexecutionMutationVariables,
} from './types/RunUtils.types';
import {
  BulkActionStatus,
  ExecutionParams,
  ExecutionTag,
  ReexecutionStrategy,
  Run,
} from '../graphql/types';
import {showLaunchError} from '../launchpad/showLaunchError';
import {
  CheckBackfillStatusQuery,
  CheckBackfillStatusQueryVariables,
} from './types/useJobReExecution.types';
import {buildLaunchPipelineReexecutionSuccessMock} from '../__fixtures__/Reexecution.fixtures';
import {EditableTagList, validateTagEditState} from '../launchpad/TagEditor';

describe('useJobReexecution', () => {
  it('creates the correct mutation for FROM_FAILURE', async () => {
    const wrapper = ({children}: {children: ReactNode}) => (
      <MockedProvider
        addTypename={false}
        mocks={[
          buildLaunchPipelineReexecutionSuccessMock({
            parentRunId: '1',
            extraTags: [{key: 'a', value: 'b'}],
          }),
        ]}
      >
        {children}
      </MockedProvider>
    );

    const {result} = renderHook(() => useJobReexecution(), {wrapper});

    await result.current.onClick(
      {id: '1', pipelineName: 'abc', tags: [{key: 'a', value: 'b'}]},
      'FROM_FAILURE',
      true,
    );

    expect(screen.findByText('Re-executed runs inherit tags'));
  });
});

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

  const [dialogProps, setDialogProps] = useState<ReexecutionEditTagsDialogProps | null>(null);
  const onClick = useCallback(
    async (
      run: Pick<Run, 'id' | 'pipelineName' | 'tags'>,
      param: ReexecutionStrategy | ExecutionParams,
      forceLaunchpad: boolean,
    ) => {
      const backfillTag = run.tags.find((t) => t.key === DagsterTag.Backfill);

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

      const launch = async (variables: LaunchPipelineReexecutionMutationVariables) => {
        try {
          const result = await launchPipelineReexecution({variables});
          handleLaunchResult(run.pipelineName, result.data?.launchPipelineReexecution, history, {
            preserveQuerystring: true,
            behavior: 'open',
          });
          onCompleted?.();
        } catch (error) {
          showLaunchError(error as Error);
        }
      };

      if (forceLaunchpad) {
        setDialogProps({
          tags: run.tags,
          onCancel: () => setDialogProps(null),
          onContinue: async (extraTags) => {
            setDialogProps(null);

            if (typeof param === 'string') {
              await launch({
                reexecutionParams: {
                  parentRunId: run.id,
                  strategy: param,
                  extraTags,
                },
              });
            } else {
              const em = param.executionMetadata || {};
              const extraTagKeys = new Set(extraTags.map((t) => t.key));

              await launch({
                executionParams: {
                  ...param,
                  executionMetadata: {
                    ...em,
                    tags: [
                      ...(em.tags || []).filter((t) => !extraTagKeys.has(t.key)),
                      ...extraTags,
                    ],
                  },
                },
              });
            }
          },
        });
      } else {
        await launch(
          typeof param === 'string'
            ? {reexecutionParams: {parentRunId: run.id, strategy: param}}
            : {executionParams: param},
        );
      }
    },
    [client, confirm, launchPipelineReexecution, history, onCompleted],
  );

  return {
    onClick,
    launchpadElement: dialogProps ? <ReexecutionEditTagsDialog {...dialogProps} /> : null,
  };
};

/** Ben Note: Wiring this into the existing launchpad is /messy/ - we only want to allow
 * editing tags (and possibly runConfigYaml in the future), and we need to disable everything
 * else. We also need to rewire the Launch button to run this mutation with the remaining args.
 */
interface ReexecutionEditTagsDialogProps {
  tags: ExecutionTag[];
  onContinue: (tags: ExecutionTag[]) => Promise<void>;
  onCancel: () => void;
}

const ReexecutionEditTagsDialog = (props: ReexecutionEditTagsDialogProps) => {
  const parentRunCustomTags = props.tags.filter((t) => !t.key.startsWith(DagsterTag.Namespace));
  const [tags, setTags] = useState(
    parentRunCustomTags.length === 0 ? [{key: '', value: ''}] : parentRunCustomTags,
  );
  const {toError, toSave} = validateTagEditState(tags);

  const onSave = () => {
    const parentRunValues = Object.fromEntries(parentRunCustomTags.map((t) => [t.key, t.value]));
    const toSaveModified = toSave.filter((t) => t.value !== parentRunValues[t.key]);
    if (!toError.length) {
      props.onContinue(toSaveModified);
    }
  };

  const disabled = !!toError.length;

  return (
    <Dialog
      icon="info"
      onClose={props.onCancel}
      style={{minWidth: 700}}
      title="Re-execute"
      isOpen={true}
    >
      <DialogBody>
        <Box padding={{bottom: 16}}>
          <Body>
            Re-executed runs inherit tags from the parent run automatically. Edit existing tags to
            override their values or add more tags below.
          </Body>
        </Box>
        <EditableTagList
          editState={tags}
          setEditState={setTags}
          tagsFromParentRun={parentRunCustomTags}
        />
      </DialogBody>
      <DialogFooter>
        <Button onClick={props.onCancel}>Cancel</Button>
        <Button intent="primary" onClick={onSave} disabled={disabled}>
          Launch Run
        </Button>
      </DialogFooter>
    </Dialog>
  );
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
