import {
  Box,
  Button,
  Checkbox,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  ProgressBar,
  showToast,
} from '@dagster-io/ui-components';
import chunk from 'lodash/chunk';
import {useEffect, useLayoutEffect, useReducer, useRef, useState} from 'react';

import {NavigationBlock} from './NavigationBlock';
import {TERMINATE_MUTATION} from './RunUtils';
import {gql, useApolloClient, useMutation} from '../apollo-client';
import {TerminateMutation, TerminateMutationVariables} from './types/RunUtils.types';
import {
  TerminateBatchQuery,
  TerminateBatchQueryVariables,
} from './types/TerminateAllRunsDialog.types';
import {RunsFilter, TerminateRunPolicy} from '../graphql/types';
import {testId} from '../testing/testId';

const BATCH_SIZE = 1000;

interface Props {
  isOpen: boolean;
  onClose: () => void;
  filter: RunsFilter;
  selectedRunsAllQueued: boolean;
}

type State = {
  step: 'initial' | 'terminating' | 'completed';
  policy: TerminateRunPolicy;
  terminated: number;
  errors: number;
  /** null = unknown (first fetch returned exactly BATCH_SIZE) */
  total: number | null;
};

type Action =
  | {type: 'reset'; selectedRunsAllQueued: boolean}
  | {type: 'set-policy'; policy: TerminateRunPolicy}
  | {type: 'start'}
  | {type: 'batch-fetched'; count: number}
  | {type: 'terminated'; success: number; errors: number}
  | {type: 'complete'};

const initialState = (allQueued: boolean): State => ({
  step: 'initial',
  policy: allQueued
    ? TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY
    : TerminateRunPolicy.SAFE_TERMINATE,
  terminated: 0,
  errors: 0,
  total: null,
});

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'reset':
      return initialState(action.selectedRunsAllQueued);
    case 'set-policy':
      return {...state, policy: action.policy};
    case 'start':
      return {...state, step: 'terminating', terminated: 0, errors: 0, total: null};
    case 'batch-fetched':
      if (action.count < BATCH_SIZE) {
        // We know the remaining count; if total was unknown, set it
        return {
          ...state,
          total: state.total === null ? state.terminated + action.count : state.total,
        };
      }
      return state;
    case 'terminated':
      return {
        ...state,
        terminated: state.terminated + action.success + action.errors,
        errors: state.errors + action.errors,
      };
    case 'complete':
      return {...state, step: 'completed'};
  }
};

export const TerminateAllRunsDialog = ({isOpen, onClose, filter, selectedRunsAllQueued}: Props) => {
  const [canClose, setCanClose] = useState(true);
  return (
    <Dialog
      isOpen={isOpen}
      title="Terminate all runs"
      canEscapeKeyClose={canClose}
      canOutsideClickClose={canClose}
      onClose={onClose}
    >
      <TerminateAllRunsDialogContent
        isOpen={isOpen}
        onClose={onClose}
        filter={filter}
        selectedRunsAllQueued={selectedRunsAllQueued}
        setCanClose={setCanClose}
      />
    </Dialog>
  );
};

interface ContentProps {
  isOpen: boolean;
  onClose: () => void;
  filter: RunsFilter;
  selectedRunsAllQueued: boolean;
  setCanClose: (canClose: boolean) => void;
}

const TerminateAllRunsDialogContent = ({
  isOpen,
  onClose,
  filter,
  selectedRunsAllQueued,
  setCanClose,
}: ContentProps) => {
  const [state, dispatch] = useReducer(reducer, selectedRunsAllQueued, (allQueued) =>
    initialState(allQueued),
  );

  const client = useApolloClient();
  const [terminate] = useMutation<TerminateMutation, TerminateMutationVariables>(
    TERMINATE_MUTATION,
  );

  const didCancel = useRef(false);
  useLayoutEffect(() => {
    return () => {
      didCancel.current = true;
    };
  }, []);

  useEffect(() => {
    if (isOpen) {
      dispatch({type: 'reset', selectedRunsAllQueued});
    }
  }, [isOpen, selectedRunsAllQueued]);

  useEffect(() => {
    setCanClose(state.step !== 'terminating');
  }, [state.step, setCanClose]);

  const mutate = async () => {
    dispatch({type: 'start'});

    // Fetch-terminate loop: fetch a batch, terminate it, repeat until < BATCH_SIZE returned.
    // Maximum number of iterations here just prevents runaway execution if something goes wrong.
    for (let iteration = 0; iteration < 25; iteration++) {
      if (didCancel.current) {
        return;
      }
      const {data} = await client.query<TerminateBatchQuery, TerminateBatchQueryVariables>({
        query: TERMINATE_BATCH_QUERY,
        variables: {filter, limit: BATCH_SIZE},
        fetchPolicy: 'no-cache',
      });

      if (data.pipelineRunsOrError.__typename !== 'Runs') {
        showToast({
          message: 'Sorry, an error occurred and the runs could not be fetched.',
          intent: 'danger',
        });
        break;
      }

      const runIds = data.pipelineRunsOrError.results.map((r) => r.id);
      dispatch({type: 'batch-fetched', count: runIds.length});

      if (runIds.length === 0) {
        break;
      }

      // Terminate in chunks of 75 (same as TerminationDialog)
      for (const runIdsChunk of chunk(runIds, 75)) {
        if (didCancel.current) {
          return;
        }
        const {data: terminateData} = await terminate({
          variables: {runIds: runIdsChunk, terminatePolicy: state.policy},
        });
        if (!terminateData || terminateData.terminateRuns.__typename === 'PythonError') {
          dispatch({type: 'terminated', success: 0, errors: runIdsChunk.length});
        } else {
          let success = 0;
          let errors = 0;
          for (const result of terminateData.terminateRuns.terminateRunResults) {
            if (result.__typename === 'TerminateRunSuccess') {
              success++;
            } else {
              errors++;
            }
          }
          dispatch({type: 'terminated', success, errors});
        }
      }

      // If this batch was smaller than BATCH_SIZE, we're done
      if (runIds.length < BATCH_SIZE) {
        break;
      }
    }

    dispatch({type: 'complete'});
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

  const progressContent = () => {
    switch (state.step) {
      case 'initial':
        return (
          <Box flex={{direction: 'column', gap: 16}}>
            <div>All matching runs will be terminated. Do you wish to continue?</div>
            {!selectedRunsAllQueued ? (
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
            ) : undefined}
          </Box>
        );
      case 'terminating':
      case 'completed': {
        const determinate = state.total !== null && state.total > 0;
        const value = state.total ? (state.terminated / state.total) * 100 : 100;
        const inProgress = state.step === 'terminating';
        return (
          <Box flex={{direction: 'column', gap: 8}}>
            {inProgress ? (
              <div>
                {state.total !== null
                  ? `${force ? 'Forcing termination' : 'Terminating'}… ${state.terminated} of ${state.total} runs`
                  : `${force ? 'Forcing termination' : 'Terminating'}… ${state.terminated} runs so far`}
              </div>
            ) : null}
            <ProgressBar
              value={determinate ? Math.max(10, value) : 100}
              animate={state.step === 'terminating'}
            />
            {state.step === 'terminating' ? (
              <NavigationBlock message="Termination in progress, please do not navigate away yet." />
            ) : null}
          </Box>
        );
      }
      default:
        return null;
    }
  };

  const completionContent = () => {
    if (state.step === 'initial') {
      return null;
    }
    if (state.step === 'terminating') {
      return <div>Please do not close the window or navigate away during termination.</div>;
    }

    const successCount = state.terminated - state.errors;
    return (
      <Box flex={{direction: 'column', gap: 8}}>
        {successCount > 0 ? (
          <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
            <Icon name="check_circle" color={Colors.accentGreen()} />
            <div>
              {force
                ? `Successfully forced termination for ${successCount} ${successCount === 1 ? 'run' : 'runs'}.`
                : `Successfully requested termination for ${successCount} ${successCount === 1 ? 'run' : 'runs'}.`}
            </div>
          </Box>
        ) : null}
        {state.errors > 0 ? (
          <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
            <Icon name="warning" color={Colors.accentYellow()} />
            <div>
              {force
                ? `Could not force termination for ${state.errors} ${state.errors === 1 ? 'run' : 'runs'}.`
                : `Could not request termination for ${state.errors} ${state.errors === 1 ? 'run' : 'runs'}.`}
            </div>
          </Box>
        ) : null}
      </Box>
    );
  };

  const buttons = () => {
    switch (state.step) {
      case 'initial':
        return (
          <>
            <Button intent="none" onClick={onClose}>
              Cancel
            </Button>
            <Button intent="danger" onClick={mutate} data-testid={testId('terminate-button')}>
              {force ? 'Force terminate all' : 'Terminate all'}
            </Button>
          </>
        );
      case 'terminating':
        return (
          <Button intent="danger" disabled>
            {force ? 'Forcing termination…' : 'Terminating…'}
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

  return (
    <>
      <DialogBody>
        <Box flex={{direction: 'column', gap: 24}}>
          {progressContent()}
          {completionContent()}
        </Box>
      </DialogBody>
      <DialogFooter>{buttons()}</DialogFooter>
    </>
  );
};

export const TERMINATE_BATCH_QUERY = gql`
  query TerminateBatchQuery($filter: RunsFilter!, $limit: Int!) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      ... on Runs {
        results {
          id
        }
      }
    }
  }
`;
