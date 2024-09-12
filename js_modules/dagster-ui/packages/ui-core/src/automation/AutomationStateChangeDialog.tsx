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
  onComplete: () => void;
  automations: AutomationInfo[];
}

export const AutomationStateChangeDialog = (props: Props) => {
  const {openWithIntent, onClose, onComplete, automations} = props;
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
              {`${
                count === 1 ? '1 automation' : `${count} automations`
              } will be stopped. Do you want to continue?`}
            </div>
          );
        }
        return (
          <div>
            {`${
              count === 1 ? '1 automation' : `${count} automations`
            } will be started. Do you want to continue?`}
          </div>
        );
      case 'updating':
      case 'completed':
        const value = count > 0 ? state.completion.completed / count : 1;
        return (
          <Group direction="column" spacing={8}>
            <ProgressBar intent="primary" value={Math.max(0.1, value)} animate={value < 1} />
            {state.step === 'updating' ? (
              <NavigationBlock message="Automations are being updated, please do not navigate away yet." />
            ) : null}
          </Group>
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
            ? `Start ${count === 1 ? '1 automation' : `${count} automations`}`
            : `Stop ${count === 1 ? '1 automation' : `${count} automations`}`;
        return (
          <>
            <Button onClick={onClose}>Cancel</Button>
            <Button intent="primary" onClick={mutate}>
              {label}
            </Button>
          </>
        );
      }
      case 'updating': {
        const label =
          openWithIntent === 'start'
            ? `Starting ${count === 1 ? '1 automation' : `${count} automations`}`
            : `Stopping ${count === 1 ? '1 automation' : `${count} automations`}`;
        return (
          <Button intent="primary" disabled>
            {label}
          </Button>
        );
      }
      case 'completed':
        return (
          <Button intent="primary" onClick={onClose}>
            Done
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
          Please do not close the window or navigate away while automations are being updated.
        </div>
      );
    }

    const errors = state.completion.errors;
    const errorCount = Object.keys(errors).length;
    const successCount = state.completion.completed - errorCount;

    return (
      <Group direction="column" spacing={8}>
        {successCount ? (
          <Group direction="row" spacing={8} alignItems="flex-start">
            <Icon name="check_circle" color={Colors.accentGreen()} />
            <div>
              {openWithIntent === 'start'
                ? `Successfully started ${
                    successCount === 1 ? '1 automation' : `${successCount} automations`
                  }.`
                : `Successfully stopped ${
                    successCount === 1 ? '1 automation' : `${successCount} automations`
                  }.`}
            </div>
          </Group>
        ) : null}
        {errorCount ? (
          <Group direction="column" spacing={8}>
            <Group direction="row" spacing={8} alignItems="flex-start">
              <Icon name="warning" color={Colors.accentYellow()} />
              <div>
                {openWithIntent === 'start'
                  ? `Could not start ${
                      errorCount === 1 ? '1 automation' : `${errorCount} automations`
                    }:`
                  : `Could not stop ${
                      errorCount === 1 ? '1 automation' : `${errorCount} automations`
                    }:`}
              </div>
            </Group>
            <ul style={{margin: '8px 0'}}>
              {Object.keys(errors).map((automationName) => (
                <li key={automationName}>
                  <Group direction="row" spacing={8}>
                    <strong>{automationName}:</strong>
                    {errors[automationName] ? <div>{errors[automationName]}</div> : null}
                  </Group>
                </li>
              ))}
            </ul>
          </Group>
        ) : null}
      </Group>
    );
  };

  const canQuicklyClose = state.step !== 'updating';

  return (
    <Dialog
      isOpen={openWithIntent !== 'not-open'}
      title={openWithIntent === 'start' ? 'Start automations' : 'Stop automations'}
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
