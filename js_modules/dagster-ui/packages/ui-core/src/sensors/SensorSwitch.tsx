import {gql, useMutation, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  Checkbox,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Spinner,
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
import {
  SensorStateQuery,
  SensorStateQueryVariables,
  SensorSwitchFragment,
} from './types/SensorSwitch.types';
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
  shouldFetchLatestState?: boolean;
}

export const SensorSwitch = (props: Props) => {
  const {repoAddress, sensor, size = 'large', shouldFetchLatestState} = props;
  const {
    permissions: {canStartSensor, canStopSensor},
    disabledReasons,
  } = usePermissionsForLocation(repoAddress.location);

  const {id, name} = sensor;
  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName: name,
  };

  const {data, loading} = useQuery<SensorStateQuery, SensorStateQueryVariables>(
    SENSOR_STATE_QUERY,
    {
      variables: {sensorSelector},
      skip: !shouldFetchLatestState,
    },
  );

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
  const [setSensorCursor, {loading: cursorMutationInFlight}] = useMutation<
    SetSensorCursorMutation,
    SetSensorCursorMutationVariables
  >(SET_CURSOR_MUTATION);
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
      stopSensor({variables: {id}});
    } else {
      startSensor({variables: {sensorSelector}});
    }
  };

  let status = sensor.sensorState.status;

  if (shouldFetchLatestState) {
    if (!data && loading) {
      return <Spinner purpose="body-text" />;
    }

    if (data?.sensorOrError.__typename !== 'Sensor') {
      return (
        <Tooltip content="Error loading sensor state">
          <Icon name="error" color={Colors.accentRed()} />;
        </Tooltip>
      );
    }

    status = data.sensorOrError.sensorState.status;
  }

  const running = status === InstigationStatus.RUNNING;
  const lastProcessedTimestamp = parseRunStatusSensorCursor(cursor);

  if (
    !running &&
    canStartSensor &&
    sensor.sensorType === SensorType.RUN_STATUS &&
    lastProcessedTimestamp &&
    isRunStatusSensorLagging(lastProcessedTimestamp)
  ) {
    // We are turning back on a sensor that has a persisted cursor for a position far back in time.
    // We should warn the user that this is what is happening.
    return (
      <>
        <Checkbox
          format="switch"
          disabled={toggleOnInFlight || toggleOffInFlight}
          checked={running || toggleOnInFlight}
          onChange={() => !running && setShowRunStatusWarningDialog(true)}
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
              <TimeFromNow unixTimestamp={lastProcessedTimestamp / 1000} />.
            </Box>
            To resume processing runs starting from now instead, clear the cursor before starting
            the sensor.
          </DialogBody>
          <DialogFooter topBorder>
            <Button
              onClick={() => {
                setShowRunStatusWarningDialog(false);
              }}
            >
              Cancel
            </Button>
            <Button
              disabled={toggleOnInFlight}
              onClick={() => {
                onChangeSwitch();
                setShowRunStatusWarningDialog(false);
              }}
            >
              Start sensor without clearing
            </Button>
            <Button
              intent="primary"
              disabled={cursorMutationInFlight || toggleOnInFlight}
              onClick={async () => {
                await clearCursor();
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

const isRunStatusSensorLagging = (lastProcessedTimestamp: number) => {
  return Date.now() - lastProcessedTimestamp > WARN_RUN_STATUS_SENSOR_LAG_SECONDS * 1000;
};

const parseRunStatusSensorCursor = (cursor: string | null) => {
  if (!cursor) {
    return null;
  }

  try {
    const cursorPayload = JSON.parse(cursor);
    const timestamp = cursorPayload.record_timestamp || cursorPayload.update_timestamp;
    return timestamp ? new Date(timestamp).getTime() : null;
  } catch (e) {
    return null;
  }
};

export const SENSOR_SWITCH_FRAGMENT = gql`
  fragment SensorSwitchFragment on Sensor {
    id
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

const SENSOR_STATE_QUERY = gql`
  query SensorStateQuery($sensorSelector: SensorSelector!) {
    sensorOrError(sensorSelector: $sensorSelector) {
      ... on Sensor {
        id
        sensorState {
          id
          status
        }
      }
    }
  }
`;
