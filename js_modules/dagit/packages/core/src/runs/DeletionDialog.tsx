import {useMutation} from '@apollo/client';
import {Button, Classes, Colors, Dialog, Icon, ProgressBar} from '@blueprintjs/core';
import * as React from 'react';

import {Group} from '../ui/Group';
import {Mono} from '../ui/Text';

import {NavigationBlock} from './NavitationBlock';
import {DELETE_MUTATION} from './RunUtils';
import {
  Delete,
  Delete_deletePipelineRun_PipelineRunNotFoundError,
  Delete_deletePipelineRun_PythonError,
  Delete_deletePipelineRun_UnauthorizedError,
} from './types/Delete';

export interface Props {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
  onTerminateInstead: () => void;
  selectedRuns: SelectedRuns;
}

type SelectedRuns = {[id: string]: boolean};

type Error =
  | Delete_deletePipelineRun_PythonError
  | Delete_deletePipelineRun_UnauthorizedError
  | Delete_deletePipelineRun_PipelineRunNotFoundError
  | undefined;

type DeletionDialogState = {
  step: 'initial' | 'deleting' | 'completed';
  frozenRuns: SelectedRuns;
  deletion: {completed: number; errors: {[id: string]: Error}};
};

type DeletionDialogAction =
  | {type: 'reset'; frozenRuns: SelectedRuns}
  | {type: 'start'}
  | {type: 'deletion-success'}
  | {type: 'deletion-error'; id: string; error: Error}
  | {type: 'complete'};

const initializeState = (frozenRuns: SelectedRuns): DeletionDialogState => {
  return {
    step: 'initial',
    frozenRuns,
    deletion: {completed: 0, errors: {}},
  };
};

const deletionDialogReducer = (
  prevState: DeletionDialogState,
  action: DeletionDialogAction,
): DeletionDialogState => {
  switch (action.type) {
    case 'reset':
      return initializeState(action.frozenRuns);
    case 'start':
      return {...prevState, step: 'deleting'};
    case 'deletion-success': {
      const {deletion} = prevState;
      return {
        ...prevState,
        step: 'deleting',
        deletion: {...deletion, completed: deletion.completed + 1},
      };
    }
    case 'deletion-error': {
      const {deletion} = prevState;
      return {
        ...prevState,
        step: 'deleting',
        deletion: {
          ...deletion,
          completed: deletion.completed + 1,
          errors: {...deletion.errors, [action.id]: action.error},
        },
      };
    }
    case 'complete':
      return {...prevState, step: 'completed'};
  }
};

export const DeletionDialog = (props: Props) => {
  const {isOpen, onClose, onComplete, onTerminateInstead, selectedRuns} = props;
  const frozenRuns = React.useRef<SelectedRuns>(selectedRuns);

  const [state, dispatch] = React.useReducer(
    deletionDialogReducer,
    frozenRuns.current,
    initializeState,
  );

  const runIDs = Object.keys(state.frozenRuns);
  const count = runIDs.length;
  const terminatableCount = runIDs.filter((id) => state.frozenRuns[id]).length;

  // If the dialog is newly open, update state to match the frozen list.
  React.useEffect(() => {
    if (isOpen) {
      dispatch({type: 'reset', frozenRuns: frozenRuns.current});
    }
  }, [isOpen]);

  // If the dialog is not open, update the ref so that the frozen list will be entered
  // into state the next time the dialog opens.
  React.useEffect(() => {
    if (!isOpen) {
      frozenRuns.current = selectedRuns;
    }
  }, [isOpen, selectedRuns]);

  const [destroy] = useMutation<Delete>(DELETE_MUTATION);

  const mutate = async () => {
    dispatch({type: 'start'});

    const runList = Object.keys(state.frozenRuns);
    for (let ii = 0; ii < runList.length; ii++) {
      const runId = runList[ii];
      const {data} = await destroy({variables: {runId}});

      if (data?.deletePipelineRun.__typename === 'DeletePipelineRunSuccess') {
        dispatch({type: 'deletion-success'});
      } else {
        dispatch({type: 'deletion-error', id: runId, error: data?.deletePipelineRun});
      }
    }

    dispatch({type: 'complete'});
    onComplete();
  };

  const progressContent = () => {
    switch (state.step) {
      case 'initial':
        return (
          <Group direction="column" spacing={8}>
            <div>{`${count} ${count === 1 ? 'run' : 'runs'} will be deleted.`}</div>
            <div>
              Deleting runs will not prevent them from continuing to execute, and may result in
              unexpected behavior.
            </div>
            {terminatableCount ? (
              <div>
                {terminatableCount > 1 ? (
                  <>
                    {`${terminatableCount} of these runs can be terminated. `}
                    <strong>
                      Please consider terminating these runs instead of deleting them.
                    </strong>
                  </>
                ) : (
                  <>
                    {`1 run can be terminated instead. `}
                    <strong>Please consider terminating this run instead of deleting it.</strong>
                  </>
                )}
              </div>
            ) : null}
            <div>Do you wish to continue with deletion?</div>
          </Group>
        );
      case 'deleting':
      case 'completed':
        const value = count > 0 ? state.deletion.completed / count : 1;
        return (
          <Group direction="column" spacing={8}>
            <div>Deleting…</div>
            <ProgressBar intent="primary" value={Math.max(0.1, value)} animate={value < 1} />
            {state.step === 'deleting' ? (
              <NavigationBlock message="Deletion in progress, please do not navigate away yet." />
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
        return (
          <>
            <Button intent="none" onClick={onClose}>
              Cancel
            </Button>
            <Button intent="danger" onClick={mutate}>
              {`Yes, delete ${`${count} ${count === 1 ? 'run' : 'runs'}`}`}
            </Button>
            {terminatableCount ? (
              <Button intent="primary" onClick={onTerminateInstead}>
                {`Terminate ${`${terminatableCount} ${
                  terminatableCount === 1 ? 'run' : 'runs'
                }`} instead`}
              </Button>
            ) : null}
          </>
        );
      case 'deleting':
        return (
          <Button intent="danger" disabled>
            Deleting…
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

    if (state.step === 'deleting') {
      return <div>Please do not close the window or navigate away during deletion.</div>;
    }

    const errors = state.deletion.errors;
    const errorCount = Object.keys(errors).length;
    const successCount = state.deletion.completed - errorCount;

    return (
      <Group direction="column" spacing={8}>
        {successCount ? (
          <Group direction="row" spacing={8} alignItems="flex-start">
            <Icon icon="tick-circle" iconSize={16} color={Colors.GREEN3} />
            <div>{`Successfully deleted ${successCount} ${
              successCount === 1 ? 'run' : 'runs'
            }.`}</div>
          </Group>
        ) : null}
        {errorCount ? (
          <Group direction="column" spacing={8}>
            <Group direction="row" spacing={8} alignItems="flex-start">
              <Icon icon="warning-sign" iconSize={16} color={Colors.GOLD3} />
              <div>{`Could not delete ${errorCount} ${errorCount === 1 ? 'run' : 'runs'}.`}</div>
            </Group>
            <ul>
              {Object.keys(errors).map((runId) => (
                <li key={runId}>
                  <Group direction="row" spacing={8}>
                    <Mono>{runId.slice(0, 8)}</Mono>
                    {errors[runId] ? <div>{errors[runId]?.message}</div> : null}
                  </Group>
                </li>
              ))}
            </ul>
          </Group>
        ) : null}
      </Group>
    );
  };

  const canQuicklyClose = state.step !== 'deleting';

  return (
    <Dialog
      isOpen={isOpen}
      title="Delete runs"
      canEscapeKeyClose={canQuicklyClose}
      canOutsideClickClose={canQuicklyClose}
      isCloseButtonShown={canQuicklyClose}
      onClose={onClose}
    >
      <div className={Classes.DIALOG_BODY}>
        <Group direction="column" spacing={24}>
          {progressContent()}
          {completionContent()}
        </Group>
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>{buttons()}</div>
      </div>
    </Dialog>
  );
};
