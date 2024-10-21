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
import {useMemo} from 'react';

import {SET_CURSOR_MUTATION} from './EditCursorDialog';
import {
  START_SENSOR_MUTATION,
  STOP_SENSOR_MUTATION,
  displaySensorMutationErrors,
} from './SensorMutations';
import {SENSOR_STATE_QUERY} from './SensorStateQuery';
import {gql, useMutation, useQuery} from '../apollo-client';
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
import {SensorStateQuery, SensorStateQueryVariables} from './types/SensorStateQuery.types';
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

  const repoAddressSelector = useMemo(() => repoAddressToSelector(repoAddress), [repoAddress]);

  const {id, name} = sensor;

  const variables = {
    id: sensor.id,
    selector: {
      ...repoAddressSelector,
      name,
    },
  };

  const {data, loading} = useQuery<SensorStateQuery, SensorStateQueryVariables>(
    SENSOR_STATE_QUERY,
    {variables},
  );

  const [startSensor, {loading: toggleOnInFlight}] = useMutation<
    StartSensorMutation,
    StartSensorMutationVariables
  >(START_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
    refetchQueries: [{variables, query: SENSOR_STATE_QUERY}],
    awaitRefetchQueries: true,
  });
  const [stopSensor, {loading: toggleOffInFlight}] = useMutation<
    StopRunningSensorMutation,
    StopRunningSensorMutationVariables
  >(STOP_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
    refetchQueries: [{variables, query: SENSOR_STATE_QUERY}],
    awaitRefetchQueries: true,
  });
  const [setSensorCursor, {loading: cursorMutationInFlight}] = useMutation<
    SetSensorCursorMutation,
    SetSensorCursorMutationVariables
  >(SET_CURSOR_MUTATION);
  const clearCursor = async () => {
    await setSensorCursor({
      variables: {
        sensorSelector: {
          ...repoAddressToSelector(repoAddress),
          sensorName: name,
        },
        cursor: undefined,
      },
    });
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
      startSensor({
        variables: {
          sensorSelector: {
            ...repoAddressToSelector(repoAddress),
            sensorName: name,
          },
        },
      });
    }
  };

  if (!data && loading) {
    return (
      <Box flex={{direction: 'row', justifyContent: 'center'}} style={{width: '30px'}}>
        <Spinner purpose="body-text" />
      </Box>
    );
  }

  // Status according to sensor object passed in (may be outdated if its from the workspace snapshot)
  let status = sensor.sensorState.status;
  if (
    // If the sensor was never toggled before then InstigationStateNotFoundError is returned
    // in this case we should rely on the data from the WorkspaceSnapshot.
    !['InstigationState', 'InstigationStateNotFoundError'].includes(
      data?.instigationStateOrError.__typename as any,
    )
  ) {
    return (
      <Tooltip content="Error loading sensor state">
        <Icon name="error" color={Colors.accentRed()} />;
      </Tooltip>
    );
  } else if (data?.instigationStateOrError.__typename === 'InstigationState') {
    // status according to latest data
    status = data?.instigationStateOrError.status;
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
  } catch {
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
