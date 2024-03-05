import {gql, useMutation} from '@apollo/client';
import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogBody,
  DialogFooter,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {SET_CURSOR_MUTATION} from './EditCursorDialog';
import {
  START_SENSOR_MUTATION,
  STOP_SENSOR_MUTATION,
  displaySensorMutationErrors,
} from './SensorMutations';
import {
  SetSensorCursorMutation,
  SetSensorCursorMutationVariables,
} from './types/EditCursorDialog.types';
import {
  StartSensorMutation,
  StartSensorMutationVariables,
  StopRunningSensorMutation,
  StopRunningSensorMutationVariables,
} from './types/SensorMutations.types';
import {SensorSwitchFragment} from './types/SensorSwitch.types';
import {usePermissionsForLocation} from '../app/Permissions';
import {InstigationStatus, SensorType} from '../graphql/types';
import {TimeFromNow} from '../ui/TimeFromNow';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

const WARN_RUN_STATUS_SENSOR_LAG_SECONDS = 24 * 60 * 60; // 24 hours

interface Props {
  repoAddress: RepoAddress;
  sensor: SensorSwitchFragment;
  size?: 'small' | 'large';
}

export const SensorSwitch = (props: Props) => {
  const {repoAddress, sensor, size = 'large'} = props;
  const {
    permissions: {canStartSensor, canStopSensor},
    disabledReasons,
  } = usePermissionsForLocation(repoAddress.location);

  const {jobOriginId, name, sensorState} = sensor;
  const {status, selectorId} = sensorState;
  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName: name,
  };

  const [startSensor, {loading: toggleOnInFlight}] = useMutation<
    StartSensorMutation,
    StartSensorMutationVariables
  >(START_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });
  const [stopSensor, {loading: toggleOffInFlight}] = useMutation<
    StopRunningSensorMutation,
    StopRunningSensorMutationVariables
  >(STOP_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });
  const [setSensorCursor] = useMutation<SetSensorCursorMutation, SetSensorCursorMutationVariables>(
    SET_CURSOR_MUTATION,
  );
  const clearCursor = async () => {
    await setSensorCursor({variables: {sensorSelector, cursor: undefined}});
  };
  const cursor =
    (sensor.sensorState.typeSpecificData &&
      sensor.sensorState.typeSpecificData.__typename === 'SensorData' &&
      sensor.sensorState.typeSpecificData.lastCursor) ||
    null;

  const [showRunStatusSensorWarningDialog, setShowRunStatusWarningDialog] = React.useState(false);

  const onChangeSwitch = () => {
    if (status === InstigationStatus.RUNNING) {
      stopSensor({variables: {jobOriginId, jobSelectorId: selectorId}});
    } else {
      startSensor({variables: {sensorSelector}});
    }
  };

  const running = status === InstigationStatus.RUNNING;

  if (
    !running &&
    canStartSensor &&
    sensor.sensorType === SensorType.RUN_STATUS &&
    _isRunStatusSensorLagging(cursor)
  ) {
    // We are turning back on a sensor that has a persisted cursor for a position far back in time.
    // We should warn the user that this is what is happening.
    const last_processed_timestamp = _parseRunStatusSensorCursor(cursor);
    return (
      <>
        <Checkbox
          format="switch"
          disabled={toggleOnInFlight || toggleOffInFlight}
          checked={running || toggleOnInFlight}
          onChange={() => setShowRunStatusWarningDialog(true)}
          size={size}
        />
        <Dialog
          isOpen={showRunStatusSensorWarningDialog}
          title="Run status sensor"
          canOutsideClickClose
          canEscapeKeyClose
          onClose={() => {
            setShowRunStatusWarningDialog(false);
          }}
          style={{width: '700px'}}
        >
          <DialogBody>
            <Box margin={{bottom: 16}}>
              This run status sensor will resume processing runs from{' '}
              <TimeFromNow unixTimestamp={last_processed_timestamp! / 1000} />.
            </Box>
            To instead resume processing runs starting from now, clear the cursor before starting
            the sensor.
          </DialogBody>
          <DialogFooter topBorder>
            <Button
              onClick={() => {
                setShowRunStatusWarningDialog(false);
              }}
            >
              Close
            </Button>
            <Button
              onClick={() => {
                onChangeSwitch();
                setShowRunStatusWarningDialog(false);
              }}
            >
              Start sensor without clearing
            </Button>
            <Button
              intent="primary"
              onClick={() => {
                clearCursor();
                onChangeSwitch();
                setShowRunStatusWarningDialog(false);
              }}
            >
              Clear cursor and start sensor
            </Button>
          </DialogFooter>
        </Dialog>
      </>
    );
  }

  if (canStartSensor && canStopSensor) {
    return (
      <Checkbox
        format="switch"
        disabled={toggleOnInFlight || toggleOffInFlight}
        checked={running || toggleOnInFlight}
        onChange={onChangeSwitch}
        size={size}
      />
    );
  }

  const lacksPermission = (running && !canStartSensor) || (!running && !canStopSensor);
  const disabled = toggleOffInFlight || toggleOnInFlight || lacksPermission;

  const switchElement = (
    <Checkbox
      format="switch"
      disabled={disabled}
      checked={running || toggleOnInFlight}
      onChange={onChangeSwitch}
      size={size}
    />
  );

  return lacksPermission ? (
    <Tooltip
      content={running ? disabledReasons.canStartSensor : disabledReasons.canStopSensor}
      display="flex"
    >
      {switchElement}
    </Tooltip>
  ) : (
    switchElement
  );
};

const _isRunStatusSensorLagging = (cursor: string | null) => {
  const last_processed_timestamp = _parseRunStatusSensorCursor(cursor);

  if (!last_processed_timestamp) {
    return false;
  }

  return Date.now() - last_processed_timestamp > WARN_RUN_STATUS_SENSOR_LAG_SECONDS * 1000;
};

const _parseRunStatusSensorCursor = (cursor: string | null) => {
  if (!cursor) {
    return null;
  }

  try {
    const cursor_payload = JSON.parse(cursor);
    const timestamp = cursor_payload.record_timestamp || cursor_payload.update_timestamp;
    return timestamp ? new Date(timestamp).getTime() : null;
  } catch (e) {
    return null;
  }
};

export const SENSOR_SWITCH_FRAGMENT = gql`
  fragment SensorSwitchFragment on Sensor {
    id
    jobOriginId
    name
    sensorState {
      id
      selectorId
      status
      typeSpecificData {
        ... on SensorData {
          lastCursor
        }
      }
    }
    sensorType
  }
`;
