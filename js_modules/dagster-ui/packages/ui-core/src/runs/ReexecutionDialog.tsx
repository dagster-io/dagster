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
import {tagsWithUIExecutionTags} from '../launchpad/uiExecutionTags';

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
    return '未知错误';
  }
  switch (error.__typename) {
    case 'ConflictingExecutionParamsError':
      return '执行参数冲突';
    case 'InvalidOutputError':
      return '无效输出';
    case 'InvalidStepError':
      return '无效步骤';
    case 'NoModeProvidedError':
      return '未提供模式';
    case 'PipelineNotFoundError':
      return '工作区中未找到作业';
    case 'PresetNotFoundError':
      return '未找到预设';
    case 'PythonError':
      return error.message;
    case 'RunConfigValidationInvalid':
      return '运行配置无效';
    case 'RunConflict':
      return '运行冲突';
    case 'UnauthorizedError':
      return '未授权重新执行';
    case 'InvalidSubsetError':
      return '无效的操作子集: ' + error.message;
    default:
      return '未知错误';
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
    const extraTags = tagsWithUIExecutionTags(extraTagsValidated.toSave);

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
              <div>未选择要重新执行的运行。</div>
              <div>您选择的运行可能已经执行完毕。</div>
            </Group>
          );
        }

        const message = () => {
          if (reexecutionStrategy === ReexecutionStrategy.ALL_STEPS) {
            return (
              <span>
                {`将重新执行 ${count} 个运行，`}
                <strong>包含所有步骤</strong>。是否继续？
              </span>
            );
          }
          return (
            <span>
              {`将重新执行 ${count} 个运行，`}
              <strong>从失败处开始</strong>。是否继续？
            </span>
          );
        };

        return (
          <Group direction="column" spacing={16}>
            <div>{message()}</div>

            <div>
              重新执行的运行会自动继承父运行的标签。如需更改标签值或添加额外标签，请在下方添加。
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
                  <>其中一个或多个运行属于某个回填</>
                ) : (
                  <>
                    其中一个或多个运行属于回填{' '}
                    {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
                    <Link to={getBackfillPath(selectedRunBackfillIds[0]!, 'runs')}>
                      {selectedRunBackfillIds[0]}
                    </Link>
                  </>
                )}
                。如果回填已完成，重新执行这些运行将不会更新回填状态或启动下游依赖的运行。
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
              <NavigationBlock message="重新执行进行中，请勿离开页面。" />
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
            <Button
              intent="primary"
              onClick={mutate}
              disabled={extraTagsValidated.toError.length > 0}
            >
              {`重新执行 ${count} 个运行`}
            </Button>
          </>
        );
      case 'reexecuting':
        return (
          <Button intent="primary" disabled>
            {`正在重新执行 ${count} 个运行...`}
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

    if (state.step === 'reexecuting') {
      return <div>重新执行过程中请勿关闭窗口或离开页面。</div>;
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
              {`已成功请求重新执行 ${successCount} 个运行。`}
            </div>
          </Group>
        ) : null}
        {errorCount ? (
          <Group direction="column" spacing={8}>
            <Group direction="row" spacing={8} alignItems="flex-start">
              <Icon name="warning" color={Colors.accentYellow()} />
              <div>
                {`无法请求重新执行 ${errorCount} 个运行：`}
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
          ? '重新执行运行'
          : '从失败处重新执行运行'
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
