// eslint-disable-next-line no-restricted-imports
import {ProgressBar} from '@blueprintjs/core';
import {
  Box,
  Button,
  Checkbox,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Group,
  Icon,
  Mono,
  showToast,
} from '@dagster-io/ui-components';
import chunk from 'lodash/chunk';
import * as React from 'react';

import {NavigationBlock} from './NavigationBlock';
import {TERMINATE_MUTATION} from './RunUtils';
import {useMutation} from '../apollo-client';
import {TerminateMutation, TerminateMutationVariables} from './types/RunUtils.types';
import {TerminateRunPolicy} from '../graphql/types';
import {testId} from '../testing/testId';

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
        showToast({
          message: '抱歉，发生错误，运行无法终止。',
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
              <div>未选择要终止的运行。</div>
              <div>您选择的运行可能已经执行完毕。</div>
            </Group>
          );
        }

        return (
          <Group direction="column" spacing={16}>
            <div>
              {`将终止 ${count} 个运行。是否继续？`}
            </div>
            {state.safeTerminationPossible ? (
              <div>
                <Checkbox
                  checked={force}
                  size="small"
                  data-testid={testId('force-termination-checkbox')}
                  label="立即强制终止"
                  onChange={onToggleForce}
                />
                {force ? (
                  <Box flex={{display: 'flex', direction: 'row', gap: 8}} margin={{top: 8}}>
                    <Icon name="warning" color={Colors.accentYellow()} />
                    <div>
                      <strong>警告：</strong>运行创建的计算资源可能无法被清理。
                    </div>
                  </Box>
                ) : null}
              </div>
            ) : !props.selectedRunsAllQueued ? (
              <Group direction="row" spacing={8}>
                <Icon name="warning" color={Colors.accentYellow()} />
                <div>
                  <strong>警告：</strong>运行创建的计算资源可能无法被清理。
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
            <div>{force ? '正在强制终止...' : '正在终止...'}</div>
            <ProgressBar intent="primary" value={Math.max(0.1, value)} animate={value < 1} />
            {state.step === 'terminating' ? (
              <NavigationBlock message="终止进行中，请勿离开页面。" />
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
              确定
            </Button>
          );
        }

        return (
          <>
            <Button intent="none" onClick={onClose}>
              取消
            </Button>
            <Button intent="danger" onClick={mutate} data-testid={testId('terminate-button')}>
              {force ? `强制终止 ${count} 个运行` : `终止 ${count} 个运行`}
            </Button>
          </>
        );
      case 'terminating':
        return (
          <Button intent="danger" disabled>
            {force ? `正在强制终止 ${count} 个运行...` : `正在终止 ${count} 个运行...`}
          </Button>
        );
      case 'completed':
        return (
          <Button intent="primary" onClick={onClose}>
            完成
          </Button>
        );
    }
  };

  const completionContent = () => {
    if (state.step === 'initial') {
      return null;
    }

    if (state.step === 'terminating') {
      return <div>终止过程中请勿关闭窗口或离开页面。</div>;
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
                ? `已成功强制终止 ${successCount} 个运行。`
                : `已成功请求终止 ${successCount} 个运行。`}
            </div>
          </Group>
        ) : null}
        {errorCount ? (
          <Group direction="column" spacing={8}>
            <Group direction="row" spacing={8} alignItems="flex-start">
              <Icon name="warning" color={Colors.accentYellow()} />
              <div>
                {force
                  ? `无法强制终止 ${errorCount} 个运行：`
                  : `无法请求终止 ${errorCount} 个运行：`}
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
      title="终止运行"
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
