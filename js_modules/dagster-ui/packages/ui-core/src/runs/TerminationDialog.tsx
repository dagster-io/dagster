import {useMutation} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {ProgressBar} from '@blueprintjs/core';
import {
  Box,
  Button,
  Checkbox,
  DialogBody,
  DialogFooter,
  Dialog,
  Group,
  Icon,
  Mono,
  Colors,
} from '@dagster-io/ui-components';
import chunk from 'lodash/chunk';
import * as React from 'react';

import {getSharedToaster} from '../app/DomUtils';
import {TerminateRunPolicy} from '../graphql/types';
import {testId} from '../testing/testId';

import {NavigationBlock} from './NavigationBlock';
import {TERMINATE_MUTATION} from './RunUtils';
import {TerminateMutation, TerminateMutationVariables} from './types/RunUtils.types';

export interface Props {
  isOpen: boolean;
  onClose: () => void;

  // Fired when terimation has finished. You may want to refresh data in the parent
  // view but keep the dialog open so the user can view the results of termination.
  onComplete: (result: TerminationDialogResult) => void;

  // A map from the run ID to its `canTerminate` value
  selectedRuns: {[id: string]: boolean};
  selectedRunsAllQueued?: boolean;
}

type TerminationError = Exclude<
  Extract<
    TerminateMutation['terminateRuns'],
    {__typename: 'TerminateRunsResult'}
  >['terminateRunResults'][0],
  {__typename: 'TerminateRunSuccess'}
>;

export type TerminationDialogResult = {
  completed: number;
  errors: {[id: string]: TerminationError};
};

type TerminationDialogState = {
  policy: TerminateRunPolicy;
  safeTerminationPossible: boolean;
  runs: SelectedRuns;
  step: 'initial' | 'terminating' | 'completed';
  termination: TerminationDialogResult;
};

type SelectedRuns = {[id: string]: boolean};

const initializeState = ({
  selectedRuns,
  selectedRunsAllQueued,
}: PropsForInitializer): TerminationDialogState => {
  // If any selected runs have `canTerminate`, we don't necessarily have to force and we
  // can show the "safe" terimnation option
  const safeTerminationPossible =
    !selectedRunsAllQueued && Object.keys(selectedRuns).some((id) => selectedRuns[id]);
  return {
    safeTerminationPossible,
    policy: safeTerminationPossible
      ? TerminateRunPolicy.SAFE_TERMINATE
      : TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY,
    runs: selectedRuns,
    step: 'initial',
    termination: {completed: 0, errors: {}},
  };
};

type TerminationDialogAction =
  | {type: 'reset'; initializerProps: PropsForInitializer}
  | {type: 'set-policy'; policy: TerminateRunPolicy}
  | {type: 'start'}
  | {type: 'termination-success'}
  | {type: 'termination-error'; id: string; error: TerminationError}
  | {type: 'complete'};

const terminationDialogReducer = (
  prevState: TerminationDialogState,
  action: TerminationDialogAction,
): TerminationDialogState => {
  switch (action.type) {
    case 'reset':
      return initializeState(action.initializerProps);
    case 'set-policy':
      return {...prevState, policy: action.policy};
    case 'start':
      return {...prevState, step: 'terminating'};
    case 'termination-success': {
      const {termination} = prevState;
      return {
        ...prevState,
        step: 'terminating',
        termination: {...termination, completed: termination.completed + 1},
      };
    }
    case 'termination-error': {
      const {termination} = prevState;
      return {
        ...prevState,
        step: 'terminating',
        termination: {
          ...termination,
          completed: termination.completed + 1,
          errors: {...termination.errors, [action.id]: action.error},
        },
      };
    }
    case 'complete':
      return {...prevState, step: 'completed'};
  }
};

type PropsForInitializer = Pick<Props, 'selectedRuns' | 'selectedRunsAllQueued'>;

export const TerminationDialog = (props: Props) => {
  const {isOpen, onClose, onComplete} = props;

  // Note: The dialog captures the runs passed in `props` into reducer state because
  // runs may disappear (and no longer be passed) as they are terminated. This means
  // that when the dialog goes from isOpen=false to isOpen=true we need to reset the
  // reducer, hence the initializerPropsRef + useEffect below.
  const [state, dispatch] = React.useReducer(terminationDialogReducer, props, initializeState);

  const initializerPropsRef = React.useRef<PropsForInitializer>(props);
  initializerPropsRef.current = props;
  React.useEffect(() => {
    if (isOpen) {
      dispatch({type: 'reset', initializerProps: initializerPropsRef.current});
    }
  }, [isOpen]);

  const [terminate] = useMutation<TerminateMutation, TerminateMutationVariables>(
    TERMINATE_MUTATION,
  );

  const mutate = async () => {
    dispatch({type: 'start'});

    const runIds = Object.keys(state.runs);
    for (const runIdsChunk of chunk(runIds, 75)) {
      const {data} = await terminate({
        variables: {runIds: runIdsChunk, terminatePolicy: state.policy},
      });
      if (!data || data?.terminateRuns.__typename === 'PythonError') {
        (await getSharedToaster()).show({
          message: 'Sorry, an error occurred and the runs could not be terminated.',
          intent: 'danger',
        });
        return;
      }
      data.terminateRuns.terminateRunResults.forEach((result, idx) => {
        const runId = runIdsChunk[idx];
        if (!runId) {
          return;
        }
        if (result.__typename === 'TerminateRunSuccess') {
          dispatch({type: 'termination-success'});
        } else {
          dispatch({type: 'termination-error', id: runId, error: result});
        }
      });
    }

    dispatch({type: 'complete'});
    onComplete(state.termination);
  };

  const onToggleForce = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch({
      type: 'set-policy',
      policy: event.target.checked
        ? TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY
        : TerminateRunPolicy.SAFE_TERMINATE,
    });
  };

  const force = state.policy === TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY;
  const count = Object.keys(state.runs).length;

  const progressContent = () => {
    switch (state.step) {
      case 'initial':
        if (!count) {
          return (
            <Group direction="column" spacing={16}>
              <div>No runs selected for termination.</div>
              <div>The runs you selected may already have finished executing.</div>
            </Group>
          );
        }

        return (
          <Group direction="column" spacing={16}>
            <div>
              {`${count} ${
                count === 1 ? 'run' : 'runs'
              } will be terminated. Do you wish to continue?`}
            </div>
            {state.safeTerminationPossible ? (
              <div>
                <Checkbox
                  checked={force}
                  size="small"
                  data-testid={testId('force-termination-checkbox')}
                  label="Force termination immediately"
                  onChange={onToggleForce}
                />
                {force ? (
                  <Box flex={{display: 'flex', direction: 'row', gap: 8}} margin={{top: 8}}>
                    <Icon name="warning" color={Colors.accentYellow()} />
                    <div>
                      <strong>Warning:</strong> computational resources created by runs may not be
                      cleaned up.
                    </div>
                  </Box>
                ) : null}
              </div>
            ) : !props.selectedRunsAllQueued ? (
              <Group direction="row" spacing={8}>
                <Icon name="warning" color={Colors.accentYellow()} />
                <div>
                  <strong>Warning:</strong> computational resources created by runs may not be
                  cleaned up.
                </div>
              </Group>
            ) : undefined}
          </Group>
        );
      case 'terminating':
      case 'completed':
        const value = count > 0 ? state.termination.completed / count : 1;
        return (
          <Group direction="column" spacing={8}>
            <div>{force ? 'Forcing termination…' : 'Terminating…'}</div>
            <ProgressBar intent="primary" value={Math.max(0.1, value)} animate={value < 1} />
            {state.step === 'terminating' ? (
              <NavigationBlock message="Termination in progress, please do not navigate away yet." />
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
            <Button intent="danger" onClick={mutate} data-testid={testId('terminate-button')}>
              {`${force ? 'Force termination for' : 'Terminate'} ${`${count} ${
                count === 1 ? 'run' : 'runs'
              }`}`}
            </Button>
          </>
        );
      case 'terminating':
        return (
          <Button intent="danger" disabled>
            {force
              ? `Forcing termination for ${`${count} ${count === 1 ? 'run' : 'runs'}...`}`
              : `Terminating ${`${count} ${count === 1 ? 'run' : 'runs'}...`}`}
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

    if (state.step === 'terminating') {
      return <div>Please do not close the window or navigate away during termination.</div>;
    }

    const errors = state.termination.errors;
    const errorCount = Object.keys(errors).length;
    const successCount = state.termination.completed - errorCount;

    return (
      <Group direction="column" spacing={8}>
        {successCount ? (
          <Group direction="row" spacing={8} alignItems="flex-start">
            <Icon name="check_circle" color={Colors.accentGreen()} />
            <div>
              {force
                ? `Successfully forced termination for ${successCount} ${
                    successCount === 1 ? 'run' : `runs`
                  }.`
                : `Successfully requested termination for ${successCount} ${
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
                {force
                  ? `Could not force termination for ${errorCount} ${
                      errorCount === 1 ? 'run' : 'runs'
                    }:`
                  : `Could not request termination for ${errorCount} ${
                      errorCount === 1 ? 'run' : 'runs'
                    }:`}
              </div>
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

  const canQuicklyClose = state.step !== 'terminating';

  return (
    <Dialog
      isOpen={isOpen}
      title="Terminate runs"
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
