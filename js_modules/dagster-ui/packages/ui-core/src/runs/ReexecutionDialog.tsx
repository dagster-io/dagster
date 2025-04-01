// eslint-disable-next-line no-restricted-imports
import {ProgressBar} from '@blueprintjs/core';
import {
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Group,
  Icon,
  Mono,
} from '@dagster-io/ui-components';
import {useEffect, useReducer, useRef} from 'react';
import {Link} from 'react-router-dom';

import {NavigationBlock} from './NavigationBlock';
import {LAUNCH_PIPELINE_REEXECUTION_MUTATION} from './RunUtils';
import {useMutation} from '../apollo-client';
import {getBackfillPath} from './RunsFeedUtils';
import {EditableTagList, validateTagEditState} from '../launchpad/TagEditor';
import {
  LaunchPipelineReexecutionMutation,
  LaunchPipelineReexecutionMutationVariables,
} from './types/RunUtils.types';
import {ExecutionTag, ReexecutionStrategy} from '../graphql/types';

export interface ReexecutionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (reexecutionState: ReexecutionState) => void;
  selectedRuns: {[id: string]: string};
  selectedRunBackfillIds: string[];
  reexecutionStrategy: ReexecutionStrategy;
}

const refineToError = (data: LaunchPipelineReexecutionMutation | null | undefined) => {
  if (data?.launchPipelineReexecution.__typename === 'LaunchRunSuccess') {
    throw new Error('Not an error!');
  }
  return data?.launchPipelineReexecution;
};

type Error = ReturnType<typeof refineToError>;

const errorText = (error: Error) => {
  if (!error) {
    return 'Unknown error';
  }
  switch (error.__typename) {
    case 'ConflictingExecutionParamsError':
      return 'Conflicting execution parameters';
    case 'InvalidOutputError':
      return 'Invalid output';
    case 'InvalidStepError':
      return 'Invalid step';
    case 'NoModeProvidedError':
      return 'No mode provided';
    case 'PipelineNotFoundError':
      return 'Job not found in workspace';
    case 'PresetNotFoundError':
      return 'Preset not found';
    case 'PythonError':
      return error.message;
    case 'RunConfigValidationInvalid':
      return 'Run config invalid';
    case 'RunConflict':
      return 'Run conflict';
    case 'UnauthorizedError':
      return 'Re-execution not authorized';
    case 'InvalidSubsetError':
      return 'Invalid op subset: ' + error.message;
    default:
      return 'Unknown error';
  }
};

type ReexecutionState = {completed: number; errors: {[id: string]: Error}};

type ReexecutionDialogState = {
  frozenRuns: SelectedRuns;
  step: 'initial' | 'reexecuting' | 'completed';
  reexecution: ReexecutionState;
  extraTags: ExecutionTag[];
};

type SelectedRuns = {[id: string]: string};

const initializeState = (selectedRuns: SelectedRuns): ReexecutionDialogState => {
  return {
    frozenRuns: selectedRuns,
    step: 'initial',
    reexecution: {completed: 0, errors: {}},
    extraTags: [],
  };
};

type ReexecutionDialogAction =
  | {type: 'reset'; frozenRuns: SelectedRuns}
  | {type: 'set-extra-tags'; tags: ExecutionTag[]}
  | {type: 'start'}
  | {type: 'reexecution-success'}
  | {type: 'reexecution-error'; id: string; error: Error}
  | {type: 'complete'};

const reexecutionDialogReducer = (
  prevState: ReexecutionDialogState,
  action: ReexecutionDialogAction,
): ReexecutionDialogState => {
  switch (action.type) {
    case 'reset':
      return initializeState(action.frozenRuns);
    case 'set-extra-tags':
      return {...prevState, extraTags: action.tags};
    case 'start':
      return {...prevState, step: 'reexecuting'};
    case 'reexecution-success': {
      const {reexecution} = prevState;
      return {
        ...prevState,
        step: 'reexecuting',
        reexecution: {...reexecution, completed: reexecution.completed + 1},
      };
    }
    case 'reexecution-error': {
      const {reexecution} = prevState;
      return {
        ...prevState,
        step: 'reexecuting',
        reexecution: {
          ...reexecution,
          completed: reexecution.completed + 1,
          errors: {...reexecution.errors, [action.id]: action.error},
        },
      };
    }
    case 'complete':
      return {...prevState, step: 'completed'};
  }
};

export const ReexecutionDialog = (props: ReexecutionDialogProps) => {
  const {isOpen, onClose, onComplete, reexecutionStrategy, selectedRuns, selectedRunBackfillIds} =
    props;

  // Freeze the selected IDs, since the list may change as runs continue processing and
  // re-executing. We want to preserve the list we're given.
  const frozenRuns = useRef<SelectedRuns>(selectedRuns);

  const [state, dispatch] = useReducer(
    reexecutionDialogReducer,
    frozenRuns.current,
    initializeState,
  );

  const extraTagsValidated = validateTagEditState(state.extraTags);
  const count = Object.keys(state.frozenRuns).length;

  // If the dialog is newly open, update state to match the frozen list.
  useEffect(() => {
    if (isOpen) {
      dispatch({type: 'reset', frozenRuns: frozenRuns.current});
    }
  }, [isOpen]);

  // If the dialog is not open, update the ref so that the frozen list will be entered
  // into state the next time the dialog opens.
  useEffect(() => {
    if (!isOpen) {
      frozenRuns.current = selectedRuns;
    }
  }, [isOpen, selectedRuns]);

  const [reexecute] = useMutation<
    LaunchPipelineReexecutionMutation,
    LaunchPipelineReexecutionMutationVariables
  >(LAUNCH_PIPELINE_REEXECUTION_MUTATION);

  const mutate = async () => {
    dispatch({type: 'start'});

    const runList = Object.keys(state.frozenRuns);
    const extraTags = extraTagsValidated.toSave.length ? extraTagsValidated.toSave : undefined;

    for (const runId of runList) {
      const {data} = await reexecute({
        variables: {
          reexecutionParams: {
            parentRunId: runId,
            strategy: reexecutionStrategy,
            extraTags,
          },
        },
      });

      if (data?.launchPipelineReexecution.__typename === 'LaunchRunSuccess') {
        dispatch({type: 'reexecution-success'});
      } else {
        dispatch({type: 'reexecution-error', id: runId, error: refineToError(data)});
      }
    }

    dispatch({type: 'complete'});
    onComplete(state.reexecution);
  };

  const progressContent = () => {
    switch (state.step) {
      case 'initial':
        if (!count) {
          return (
            <Group direction="column" spacing={16}>
              <div>No runs selected for re-execution.</div>
              <div>The runs you selected may already have finished executing.</div>
            </Group>
          );
        }

        const message = () => {
          if (reexecutionStrategy === ReexecutionStrategy.ALL_STEPS) {
            return (
              <span>
                {`${count} ${count === 1 ? 'run' : 'runs'} will be re-executed `}
                <strong>with all steps</strong>. Do you wish to continue?
              </span>
            );
          }
          return (
            <span>
              {`${count} ${count === 1 ? 'run' : 'runs'} will be re-executed `}
              <strong>from failure</strong>. Do you wish to continue?
            </span>
          );
        };

        return (
          <Group direction="column" spacing={16}>
            <div>{message()}</div>

            <div>
              Re-executed runs inherit tags from the parent runs automatically. To change tag values
              or add additional tags, add them below.
            </div>
            <EditableTagList
              editState={state.extraTags}
              setEditState={(cb) =>
                dispatch({
                  type: 'set-extra-tags',
                  tags: cb instanceof Array ? cb : cb(state.extraTags),
                })
              }
            />

            {selectedRunBackfillIds.length > 0 ? (
              <div>
                {selectedRunBackfillIds.length > 1 ? (
                  <>One or more of these runs is part of a backfill</>
                ) : (
                  <>
                    One or more of these runs is part of backfill{' '}
                    <Link to={getBackfillPath(selectedRunBackfillIds[0]!, false)}>
                      {selectedRunBackfillIds[0]}
                    </Link>
                  </>
                )}
                . If the backfill has completed, re-executing these runs will not update the
                backfill status or launch runs of downstream dependencies.
              </div>
            ) : undefined}
          </Group>
        );
      case 'reexecuting':
      case 'completed':
        const value = count > 0 ? state.reexecution.completed / count : 1;
        return (
          <Group direction="column" spacing={8}>
            <ProgressBar intent="primary" value={Math.max(0.1, value)} animate={value < 1} />
            {state.step === 'reexecuting' ? (
              <NavigationBlock message="Re-execution in progress, please do not navigate away yet." />
            ) : null}
          </Group>
        );
      default:
        return null;
    }
  };

  const buttons = () => {
    switch (state.step) {
      case 'initial':
        if (!count) {
          return (
            <Button intent="none" onClick={onClose}>
              OK
            </Button>
          );
        }

        return (
          <>
            <Button intent="none" onClick={onClose}>
              Cancel
            </Button>
            <Button
              intent="primary"
              onClick={mutate}
              disabled={extraTagsValidated.toError.length > 0}
            >
              {`Re-execute ${`${count} ${count === 1 ? 'run' : 'runs'}`}`}
            </Button>
          </>
        );
      case 'reexecuting':
        return (
          <Button intent="primary" disabled>
            {`Re-executing ${`${count} ${count === 1 ? 'run' : 'runs'}...`}`}
          </Button>
        );
      case 'completed':
        return (
          <Button intent="primary" onClick={onClose}>
            Done
          </Button>
        );
    }
  };

  const completionContent = () => {
    if (state.step === 'initial') {
      return null;
    }

    if (state.step === 'reexecuting') {
      return <div>Please do not close the window or navigate away during re-execution.</div>;
    }

    const errors = state.reexecution.errors;
    const errorCount = Object.keys(errors).length;
    const successCount = state.reexecution.completed - errorCount;

    return (
      <Group direction="column" spacing={8}>
        {successCount ? (
          <Group direction="row" spacing={8} alignItems="flex-start">
            <Icon name="check_circle" color={Colors.accentGreen()} />
            <div>
              {`Successfully requested re-execution for ${successCount} ${
                successCount === 1 ? 'run' : `runs`
              }.`}
            </div>
          </Group>
        ) : null}
        {errorCount ? (
          <Group direction="column" spacing={8}>
            <Group direction="row" spacing={8} alignItems="flex-start">
              <Icon name="warning" color={Colors.accentYellow()} />
              <div>
                {`Could not request re-execution for ${errorCount} ${
                  errorCount === 1 ? 'run' : 'runs'
                }:`}
              </div>
            </Group>
            <ul>
              {Object.keys(errors).map((runId) => (
                <li key={runId}>
                  <Group direction="row" spacing={8} alignItems="baseline">
                    <Mono>{runId.slice(0, 8)}</Mono>
                    {errors[runId] ? <div>{errorText(errors[runId])}</div> : null}
                  </Group>
                </li>
              ))}
            </ul>
          </Group>
        ) : null}
      </Group>
    );
  };

  const canQuicklyClose = state.step !== 'reexecuting';

  return (
    <Dialog
      style={{minWidth: 590}}
      isOpen={isOpen}
      title={
        reexecutionStrategy === ReexecutionStrategy.ALL_STEPS
          ? 'Re-execute runs'
          : 'Re-execute runs from failure'
      }
      canEscapeKeyClose={canQuicklyClose}
      canOutsideClickClose={canQuicklyClose}
      onClose={onClose}
    >
      <DialogBody>
        <Group direction="column" spacing={24}>
          {progressContent()}
          {completionContent()}
        </Group>
      </DialogBody>
      <DialogFooter>{buttons()}</DialogFooter>
    </Dialog>
  );
};
