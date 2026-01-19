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

import {useMutation} from '../apollo-client';
import {assertUnreachable} from '../app/Util';
import {
  OpenWithIntent,
  useInstigationStateReducer,
} from '../instigation/useInstigationStateReducer';
import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';
import {NavigationBlock} from '../runs/NavigationBlock';
import {START_SCHEDULE_MUTATION, STOP_SCHEDULE_MUTATION} from '../schedules/ScheduleMutations';
import {
  StartThisScheduleMutation,
  StartThisScheduleMutationVariables,
  StopScheduleMutation,
  StopScheduleMutationVariables,
} from '../schedules/types/ScheduleMutations.types';
import {START_SENSOR_MUTATION, STOP_SENSOR_MUTATION} from '../sensors/SensorMutations';
import {
  StartSensorMutation,
  StartSensorMutationVariables,
  StopRunningSensorMutation,
  StopRunningSensorMutationVariables,
} from '../sensors/types/SensorMutations.types';
import {RepoAddress} from '../workspace/types';

export interface AutomationInfo {
  repoAddress: RepoAddress;
  name: string;
  type: 'sensor' | 'schedule';
  instigationState: BasicInstigationStateFragment;
}

export interface Props {
  openWithIntent: OpenWithIntent;
  onClose: () => void;
  automations: AutomationInfo[];
}

export const AutomationStateChangeDialog = (props: Props) => {
  const {openWithIntent, onClose, automations} = props;
  const count = automations.length;

  const [state, dispatch] = useInstigationStateReducer();

  // If the dialog is newly closed, reset state.
  useEffect(() => {
    if (openWithIntent === 'not-open') {
      dispatch({type: 'reset'});
    }
  }, [openWithIntent, dispatch]);

  const [startSensor] = useMutation<StartSensorMutation, StartSensorMutationVariables>(
    START_SENSOR_MUTATION,
  );

  const [stopSensor] = useMutation<StopRunningSensorMutation, StopRunningSensorMutationVariables>(
    STOP_SENSOR_MUTATION,
  );

  const [startSchedule] = useMutation<
    StartThisScheduleMutation,
    StartThisScheduleMutationVariables
  >(START_SCHEDULE_MUTATION);

  const [stopSchedule] = useMutation<StopScheduleMutation, StopScheduleMutationVariables>(
    STOP_SCHEDULE_MUTATION,
  );

  const start = async (automation: AutomationInfo) => {
    const {repoAddress, name, type} = automation;
    const repoValues = {
      repositoryLocationName: repoAddress.location,
      repositoryName: repoAddress.name,
    };

    switch (type) {
      case 'sensor': {
        const {data} = await startSensor({
          variables: {sensorSelector: {...repoValues, sensorName: name}},
        });

        switch (data?.startSensor.__typename) {
          case 'Sensor':
            dispatch({type: 'update-success'});
            return;
          case 'SensorNotFoundError':
          case 'UnauthorizedError':
          case 'PythonError':
            dispatch({
              type: 'update-error',
              name,
              error: data.startSensor.message,
            });
        }

        break;
      }

      case 'schedule': {
        const {data} = await startSchedule({
          variables: {scheduleSelector: {...repoValues, scheduleName: name}},
        });

        switch (data?.startSchedule.__typename) {
          case 'ScheduleStateResult':
            dispatch({type: 'update-success'});
            return;
          case 'UnauthorizedError':
          case 'PythonError':
            dispatch({
              type: 'update-error',
              name,
              error: data.startSchedule.message,
            });
        }

        break;
      }

      default:
        assertUnreachable(type);
    }
  };

  const stop = async (automation: AutomationInfo) => {
    const {name, type, instigationState} = automation;
    const variables = {id: instigationState.id};

    switch (type) {
      case 'sensor': {
        const {data} = await stopSensor({variables});
        switch (data?.stopSensor.__typename) {
          case 'StopSensorMutationResult':
            dispatch({type: 'update-success'});
            return;
          case 'UnauthorizedError':
          case 'PythonError':
            dispatch({
              type: 'update-error',
              name,
              error: data.stopSensor.message,
            });
        }
        break;
      }

      case 'schedule': {
        const {data} = await stopSchedule({variables});
        switch (data?.stopRunningSchedule.__typename) {
          case 'ScheduleStateResult':
            dispatch({type: 'update-success'});
            return;
          case 'UnauthorizedError':
          case 'PythonError':
            dispatch({
              type: 'update-error',
              name,
              error: data.stopRunningSchedule.message,
            });
        }
        break;
      }

      default:
        assertUnreachable(type);
    }
  };

  const mutate = async () => {
    if (openWithIntent === 'not-open') {
      return;
    }

    dispatch({type: 'start'});
    for (const automation of automations) {
      if (openWithIntent === 'start') {
        await start(automation);
      } else {
        await stop(automation);
      }
    }

    dispatch({type: 'complete'});
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
              {`将停止 ${count === 1 ? '1 个自动化' : `${count} 个自动化`}。是否继续？`}
            </div>
          );
        }
        return (
          <div>
            {`将启动 ${count === 1 ? '1 个自动化' : `${count} 个自动化`}。是否继续？`}
          </div>
        );
      case 'updating':
      case 'completed':
        const value = count > 0 ? state.completion.completed / count : 1;
        return (
          <Box flex={{direction: 'column', gap: 8}}>
            <ProgressBar value={Math.max(0.1, value) * 100} animate={value < 1} />
            {state.step === 'updating' ? (
              <NavigationBlock message="正在更新自动化，请勿离开此页面。" />
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
            ? `启动 ${count === 1 ? '1 个自动化' : `${count} 个自动化`}`
            : `停止 ${count === 1 ? '1 个自动化' : `${count} 个自动化`}`;
        return (
          <>
            <Button onClick={onClose}>取消</Button>
            <Button intent="primary" onClick={mutate}>
              {label}
            </Button>
          </>
        );
      }
      case 'updating': {
        const label =
          openWithIntent === 'start'
            ? `正在启动 ${count === 1 ? '1 个自动化' : `${count} 个自动化`}`
            : `正在停止 ${count === 1 ? '1 个自动化' : `${count} 个自动化`}`;
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
          正在更新自动化，请勿关闭窗口或离开页面。
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
                ? `已成功启动 ${successCount === 1 ? '1 个自动化' : `${successCount} 个自动化`}。`
                : `已成功停止 ${successCount === 1 ? '1 个自动化' : `${successCount} 个自动化`}。`}
            </div>
          </Box>
        ) : null}
        {errorCount ? (
          <Box flex={{direction: 'column', gap: 8}}>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
              <Icon name="warning" color={Colors.accentYellow()} />
              <div>
                {openWithIntent === 'start'
                  ? `无法启动 ${errorCount === 1 ? '1 个自动化' : `${errorCount} 个自动化`}：`
                  : `无法停止 ${errorCount === 1 ? '1 个自动化' : `${errorCount} 个自动化`}：`}
              </div>
            </Box>
            <ul style={{margin: '8px 0'}}>
              {Object.keys(errors).map((automationName) => (
                <li key={automationName}>
                  <Box flex={{direction: 'row', gap: 8}}>
                    <strong>{automationName}:</strong>
                    {errors[automationName] ? <div>{errors[automationName]}</div> : null}
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
      title={openWithIntent === 'start' ? '启动自动化' : '停止自动化'}
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
