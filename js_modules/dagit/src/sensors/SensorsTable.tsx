import {useMutation} from '@apollo/client';
import {Colors, Icon, Tooltip} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from 'src/jobs/JobTick';
import {JobRunStatus} from 'src/jobs/JobUtils';
import {humanizeSensorInterval} from 'src/sensors/SensorDetails';
import {
  displaySensorMutationErrors,
  START_SENSOR_MUTATION,
  STOP_SENSOR_MUTATION,
} from 'src/sensors/SensorMutations';
import {SensorFragment} from 'src/sensors/types/SensorFragment';
import {StartSensor} from 'src/sensors/types/StartSensor';
import {StopSensor} from 'src/sensors/types/StopSensor';
import {JobStatus, JobType} from 'src/types/globalTypes';
import {Group} from 'src/ui/Group';
import {SwitchWithoutLabel} from 'src/ui/SwitchWithoutLabel';
import {Table} from 'src/ui/Table';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

export const SensorsTable: React.FC<{
  repoAddress: RepoAddress;
  sensors: SensorFragment[];
}> = ({repoAddress, sensors}) => {
  const lastTick = 'Status of the last tick: One of `Started`, `Skipped`, `Requested`, `Failed`';
  const lastRun = 'The status of the last run requested by this sensor';
  const partitionStatus = (
    <div style={{width: '300px'}}>
      <Group direction="column" spacing={12}>
        <div>The status of each partition in the partition set associated with this sensor.</div>
        <div>
          Partitions have a `Success` status if the last run for that partition completed
          successfully.
        </div>
        <div>
          Partitions have a `Missing` status if no run has been executed for that partition.
        </div>
      </Group>
    </div>
  );
  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '60px'}}></th>
          <th style={{width: '300px'}}>Sensor Name</th>
          <th style={{width: '150px'}}>Frequency</th>
          <th style={{width: '120px'}}>
            <Group direction="row" spacing={8} alignItems="center">
              Last tick
              <Tooltip position="top" content={lastTick}>
                <Icon
                  icon={IconNames.INFO_SIGN}
                  iconSize={12}
                  style={{position: 'relative', top: '-2px'}}
                />
              </Tooltip>
            </Group>
          </th>
          <th>
            <Group direction="row" spacing={8} alignItems="center">
              Last Run
              <Tooltip position="top" content={lastRun}>
                <Icon
                  icon={IconNames.INFO_SIGN}
                  iconSize={12}
                  style={{position: 'relative', top: '-2px'}}
                />
              </Tooltip>
            </Group>
          </th>
          <th>
            <Group direction="row" spacing={8} alignItems="center">
              Partition status
              <Tooltip position="top" content={partitionStatus}>
                <Icon
                  icon={IconNames.INFO_SIGN}
                  iconSize={12}
                  style={{position: 'relative', top: '-2px'}}
                />
              </Tooltip>
            </Group>
          </th>
          <th>Execution Params</th>
        </tr>
      </thead>
      <tbody>
        {sensors.map((sensor) => (
          <SensorRow key={sensor.name} repoAddress={repoAddress} sensor={sensor} />
        ))}
      </tbody>
    </Table>
  );
};

const SensorRow: React.FC<{
  repoAddress: RepoAddress;
  sensor: SensorFragment;
}> = ({repoAddress, sensor}) => {
  const {name, mode, pipelineName, sensorState} = sensor;
  const {status, ticks} = sensorState;
  const latestTick = ticks.length ? ticks[0] : null;

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

  return (
    <tr key={name}>
      <td>
        <SwitchWithoutLabel
          disabled={toggleOnInFlight || toggleOffInFlight}
          large
          innerLabelChecked="on"
          innerLabel="off"
          checked={status === JobStatus.RUNNING}
          onChange={onChangeSwitch}
        />
      </td>
      <td>
        <Group direction="column" spacing={4}>
          <Link to={workspacePathFromAddress(repoAddress, `/sensors/${name}`)}>{name}</Link>
          <Group direction="row" spacing={4} alignItems="center">
            <Icon
              icon="diagram-tree"
              color={Colors.GRAY2}
              iconSize={12}
              style={{position: 'relative', top: '-2px'}}
            />
            <span style={{fontSize: '13px'}}>
              <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/`)}>
                {pipelineName}
              </Link>
            </span>
          </Group>
        </Group>
      </td>
      <td>{humanizeSensorInterval(sensor.minIntervalSeconds)}</td>
      <td>
        {latestTick ? (
          <TickTag tick={latestTick} jobType={JobType.SENSOR} />
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
        )}
      </td>
      <td>
        <div style={{display: 'flex'}}>
          <JobRunStatus jobState={sensorState} />
        </div>
      </td>
      <td>
        <span style={{color: Colors.GRAY4}}>None</span>
      </td>
      <td>
        <div style={{display: 'flex', alignItems: 'center'}}>
          <div>{`Mode: ${mode}`}</div>
        </div>
      </td>
    </tr>
  );
};
