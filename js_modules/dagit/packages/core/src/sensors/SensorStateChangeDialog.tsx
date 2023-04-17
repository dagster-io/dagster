import {useMutation} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {ProgressBar} from '@blueprintjs/core';
import {Button, Colors, DialogBody, DialogFooter, Dialog, Group, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {
  OpenWithIntent,
  useInstigationStateReducer,
} from '../instigation/useInstigationStateReducer';
import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';
import {NavigationBlock} from '../runs/NavigationBlock';
import {RepoAddress} from '../workspace/types';

import {START_SENSOR_MUTATION, STOP_SENSOR_MUTATION} from './SensorMutations';
import {
  StartSensorMutation,
  StartSensorMutationVariables,
  StopRunningSensorMutation,
  StopRunningSensorMutationVariables,
} from './types/SensorMutations.types';

export type SensorInfo = {
  repoAddress: RepoAddress;
  sensorName: string;
  sensorState: BasicInstigationStateFragment;
};

export interface Props {
  openWithIntent: OpenWithIntent;
  onClose: () => void;
  onComplete: () => void;
  sensors: SensorInfo[];
}

export const SensorStateChangeDialog = (props: Props) => {
  const {openWithIntent, onClose, onComplete, sensors} = props;
  const count = sensors.length;

  const [state, dispatch] = useInstigationStateReducer();

  // If the dialog is newly closed, reset state.
  React.useEffect(() => {
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

  const start = async (sensor: SensorInfo) => {
    const {repoAddress, sensorName} = sensor;
    const variables = {
      sensorSelector: {
        repositoryLocationName: repoAddress.location,
        repositoryName: repoAddress.name,
        sensorName,
      },
    };

    const {data} = await startSensor({variables});

    switch (data?.startSensor.__typename) {
      case 'Sensor':
        dispatch({type: 'update-success'});
        return;
      case 'SensorNotFoundError':
      case 'UnauthorizedError':
      case 'PythonError':
        dispatch({
          type: 'update-error',
          name: sensorName,
          error: data.startSensor.message,
        });
    }
  };

  const stop = async (sensor: SensorInfo) => {
    const {sensorName, sensorState} = sensor;
    const variables = {
      jobOriginId: sensorState.id,
      jobSelectorId: sensorState.selectorId,
    };

    const {data} = await stopSensor({variables});

    switch (data?.stopSensor.__typename) {
      case 'StopSensorMutationResult':
        dispatch({type: 'update-success'});
        return;
      case 'UnauthorizedError':
      case 'PythonError':
        dispatch({
          type: 'update-error',
          name: sensorName,
          error: data.stopSensor.message,
        });
    }
  };

  const mutate = async () => {
    if (openWithIntent === 'not-open') {
      return;
    }

    dispatch({type: 'start'});
    for (let ii = 0; ii < sensors.length; ii++) {
      const sensor = sensors[ii];
      if (openWithIntent === 'start') {
        await start(sensor);
      } else {
        await stop(sensor);
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
              {`${count} ${
                count === 1 ? 'sensor' : 'sensors'
              } will be stopped. Do you want to continue?`}
            </div>
          );
        }
        return (
          <div>
            {`${count} ${
              count === 1 ? 'sensor' : 'sensors'
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
              <NavigationBlock message="Sensors are being updated, please do not navigate away yet." />
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
            ? `Start ${count === 1 ? '1 sensor' : `${count} sensors`}`
            : `Stop ${count === 1 ? '1 sensor' : `${count} sensors`}`;
        return (
          <>
            <Button intent="none" onClick={onClose}>
              Cancel
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
            ? `Starting ${count === 1 ? '1 sensor' : `${count} sensors`}`
            : `Stopping ${count === 1 ? '1 sensor' : `${count} sensors`}`;
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
        <div>Please do not close the window or navigate away while sensors are being updated.</div>
      );
    }

    const errors = state.completion.errors;
    const errorCount = Object.keys(errors).length;
    const successCount = state.completion.completed - errorCount;

    return (
      <Group direction="column" spacing={8}>
        {successCount ? (
          <Group direction="row" spacing={8} alignItems="flex-start">
            <Icon name="check_circle" color={Colors.Green500} />
            <div>
              {openWithIntent === 'start'
                ? `Successfully started ${
                    successCount === 1 ? '1 sensor' : `${successCount} sensors`
                  }.`
                : `Successfully stopped ${
                    successCount === 1 ? '1 sensor' : `${successCount} sensors`
                  }.`}
            </div>
          </Group>
        ) : null}
        {errorCount ? (
          <Group direction="column" spacing={8}>
            <Group direction="row" spacing={8} alignItems="flex-start">
              <Icon name="warning" color={Colors.Yellow500} />
              <div>
                {openWithIntent === 'start'
                  ? `Could not start ${errorCount === 1 ? '1 sensor' : `${errorCount} sensors`}:`
                  : `Could not stop ${errorCount === 1 ? '1 sensor' : `${errorCount} sensors`}:`}
              </div>
            </Group>
            <ul style={{margin: '8px 0'}}>
              {Object.keys(errors).map((sensorName) => (
                <li key={sensorName}>
                  <Group direction="row" spacing={8}>
                    <strong>{sensorName}:</strong>
                    {errors[sensorName] ? <div>{errors[sensorName]}</div> : null}
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
      title={openWithIntent === 'start' ? 'Start sensors' : 'Stop sensors'}
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
