import {useMutation} from '@apollo/client';
import {Switch} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from 'src/JobTick';
import {TimestampDisplay} from 'src/schedules/TimestampDisplay';
import {
  displaySensorMutationErrors,
  START_SENSOR_MUTATION,
  STOP_SENSOR_MUTATION,
} from 'src/sensors/SensorMutations';
import {SensorFragment} from 'src/sensors/types/SensorFragment';
import {StartSensor} from 'src/sensors/types/StartSensor';
import {StopSensor} from 'src/sensors/types/StopSensor';
import {JobStatus, JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {MetadataTable} from 'src/ui/MetadataTable';
import {Heading} from 'src/ui/Text';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface Props {
  sensor: SensorFragment;
  repoAddress: RepoAddress;
}

export const SensorDetails = (props: Props) => {
  const {sensor, repoAddress} = props;
  const {
    name,
    pipelineName,
    sensorState: {status, ticks},
  } = sensor;

  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName: name,
  };
  const {jobOriginId} = sensor;
  const [startSensor, {loading: toggleOnInFlight}] = useMutation<StartSensor>(
    START_SENSOR_MUTATION,
    {onCompleted: displaySensorMutationErrors},
  );
  const [stopSensor, {loading: toggleOffInFlight}] = useMutation<StopSensor>(STOP_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });

  const onChangeSwitch = () => {
    if (status === JobStatus.RUNNING) {
      stopSensor({variables: {jobOriginId}});
    } else {
      startSensor({variables: {sensorSelector}});
    }
  };

  const latestTick = ticks.length ? ticks[0] : null;

  return (
    <Group direction="column" spacing={12}>
      <Group alignItems="center" direction="row" spacing={8}>
        <Heading>{name}</Heading>
        <Box margin={{left: 4}}>
          <Switch
            checked={status === JobStatus.RUNNING}
            inline
            large
            disabled={toggleOffInFlight || toggleOnInFlight}
            innerLabelChecked="on"
            innerLabel="off"
            onChange={onChangeSwitch}
            style={{margin: '4px 0 0 0'}}
          />
        </Box>
      </Group>
      <MetadataTable
        rows={[
          {
            key: 'Pipeline name',
            value: (
              <Link to={workspacePathFromAddress(repoAddress, `/pipeline/${pipelineName}`)}>
                {pipelineName}
              </Link>
            ),
          },
          {
            key: 'Latest tick',
            value: latestTick ? (
              <Group direction="row" spacing={8} alignItems="center">
                <TimestampDisplay timestamp={latestTick.timestamp} />
                <TickTag tick={latestTick} jobType={JobType.SENSOR} />
              </Group>
            ) : (
              'Sensor has never run'
            ),
          },
        ]}
      />
    </Group>
  );
};
