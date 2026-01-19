import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  ProgressBar,
} from '@dagster-io/ui-components';
import {useEffect} from 'react';

import {START_SCHEDULE_MUTATION, STOP_SCHEDULE_MUTATION} from './ScheduleMutations';
import {useMutation} from '../apollo-client';
import {
  StartThisScheduleMutation,
  StartThisScheduleMutationVariables,
  StopScheduleMutation,
  StopScheduleMutationVariables,
} from './types/ScheduleMutations.types';
import {
  OpenWithIntent,
  useInstigationStateReducer,
} from '../instigation/useInstigationStateReducer';
import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';
import {NavigationBlock} from '../runs/NavigationBlock';
import {RepoAddress} from '../workspace/types';

export type ScheduleInfo = {
  repoAddress: RepoAddress;
  scheduleName: string;
  scheduleState: BasicInstigationStateFragment;
};

export interface Props {
  openWithIntent: OpenWithIntent;
  onClose: () => void;
  onComplete: () => void;
  schedules: ScheduleInfo[];
}

export const ScheduleStateChangeDialog = (props: Props) => {
  const {openWithIntent, onClose, onComplete, schedules} = props;
  const count = schedules.length;

  const [state, dispatch] = useInstigationStateReducer();

  // If the dialog is newly closed, reset state.
  useEffect(() => {
    if (openWithIntent === 'not-open') {
      dispatch({type: 'reset'});
    }
  }, [openWithIntent, dispatch]);

  const [startSchedule] = useMutation<
    StartThisScheduleMutation,
    StartThisScheduleMutationVariables
  >(START_SCHEDULE_MUTATION);

  const [stopSchedule] = useMutation<StopScheduleMutation, StopScheduleMutationVariables>(
    STOP_SCHEDULE_MUTATION,
  );

  const start = async (schedule: ScheduleInfo) => {
    const {repoAddress, scheduleName} = schedule;
    const variables = {
      scheduleSelector: {
        repositoryLocationName: repoAddress.location,
        repositoryName: repoAddress.name,
        scheduleName,
      },
    };

    const {data} = await startSchedule({variables});

    switch (data?.startSchedule.__typename) {
      case 'ScheduleStateResult':
        dispatch({type: 'update-success'});
        return;
      case 'UnauthorizedError':
      case 'PythonError':
        dispatch({
          type: 'update-error',
          name: scheduleName,
          error: data.startSchedule.message,
        });
    }
  };

  const stop = async (schedule: ScheduleInfo) => {
    const {scheduleName, scheduleState} = schedule;
    const variables = {
      id: scheduleState.id,
    };

    const {data} = await stopSchedule({variables});

    switch (data?.stopRunningSchedule.__typename) {
      case 'ScheduleStateResult':
        dispatch({type: 'update-success'});
        return;
      case 'UnauthorizedError':
      case 'PythonError':
        dispatch({
          type: 'update-error',
          name: scheduleName,
          error: data.stopRunningSchedule.message,
        });
    }
  };

  const mutate = async () => {
    if (openWithIntent === 'not-open') {
      return;
    }

    dispatch({type: 'start'});
    for (const schedule of schedules) {
      if (openWithIntent === 'start') {
        await start(schedule);
      } else {
        await stop(schedule);
      }
    }

    dispatch({type: 'complete'});
    onComplete();
  };

  const progressContent = () => {
    if (openWithIntent === 'not-open') {
      return null;
    }

    switch (state.step) {
      case 'initial':
        if (openWithIntent === 'stop') {
          return (
            <div>
              {`将停止 ${count} 个定时任务。是否继续？`}
            </div>
          );
        }
        return (
          <div>
            {`将启动 ${count} 个定时任务。是否继续？`}
          </div>
        );
      case 'updating':
      case 'completed':
        const value = count > 0 ? state.completion.completed / count : 1;
        return (
          <Box flex={{direction: 'column', gap: 8}}>
            <ProgressBar value={Math.max(0.1, value) * 100} animate={value < 100} />
            {state.step === 'updating' ? (
              <NavigationBlock message="定时任务正在更新中，请勿离开页面。" />
            ) : null}
          </Box>
        );
      default:
        return null;
    }
  };

  const buttons = () => {
    if (openWithIntent === 'not-open') {
      return null;
    }

    switch (state.step) {
      case 'initial': {
        const label =
          openWithIntent === 'start'
            ? `启动 ${count} 个定时任务`
            : `停止 ${count} 个定时任务`;
        return (
          <>
            <Button intent="none" onClick={onClose}>
              取消
            </Button>
            <Button intent="primary" onClick={mutate}>
              {label}
            </Button>
          </>
        );
      }
      case 'updating': {
        const label =
          openWithIntent === 'start'
            ? `正在启动 ${count} 个定时任务`
            : `正在停止 ${count} 个定时任务`;
        return (
          <Button intent="primary" disabled>
            {label}
          </Button>
        );
      }
      case 'completed':
        return (
          <Button intent="primary" onClick={onClose}>
            完成
          </Button>
        );
    }
  };

  const completionContent = () => {
    if (openWithIntent === 'not-open' || state.step === 'initial') {
      return null;
    }

    if (state.step === 'updating') {
      return (
        <div>
          定时任务正在更新中，请勿关闭窗口或离开页面。
        </div>
      );
    }

    const errors = state.completion.errors;
    const errorCount = Object.keys(errors).length;
    const successCount = state.completion.completed - errorCount;

    return (
      <Box flex={{direction: 'column', gap: 8}}>
        {successCount ? (
          <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
            <Icon name="check_circle" color={Colors.accentGreen()} />
            <div>
              {openWithIntent === 'start'
                ? `成功启动 ${successCount} 个定时任务。`
                : `成功停止 ${successCount} 个定时任务。`}
            </div>
          </Box>
        ) : null}
        {errorCount ? (
          <Box flex={{direction: 'column', gap: 8}}>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
              <Icon name="warning" color={Colors.accentYellow()} />
              <div>
                {openWithIntent === 'start'
                  ? `无法启动 ${errorCount} 个定时任务。`
                  : `无法停止 ${errorCount} 个定时任务。`}
              </div>
            </Box>
            <ul>
              {Object.keys(errors).map((scheduleName) => (
                <li key={scheduleName}>
                  <Box flex={{direction: 'row', gap: 8}}>
                    <strong>{scheduleName}:</strong>
                    {errors[scheduleName] ? <div>{errors[scheduleName]}</div> : null}
                  </Box>
                </li>
              ))}
            </ul>
          </Box>
        ) : null}
      </Box>
    );
  };

  const canQuicklyClose = state.step !== 'updating';

  return (
    <Dialog
      isOpen={openWithIntent !== 'not-open'}
      title={openWithIntent === 'start' ? '启动定时任务' : '停止定时任务'}
      canEscapeKeyClose={canQuicklyClose}
      canOutsideClickClose={canQuicklyClose}
      onClose={onClose}
    >
      <DialogBody>
        <Box flex={{direction: 'column', gap: 24}}>
          {progressContent()}
          {completionContent()}
        </Box>
      </DialogBody>
      <DialogFooter>{buttons()}</DialogFooter>
    </Dialog>
  );
};
