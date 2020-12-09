import {useMutation} from '@apollo/client';
import {Colors, Switch, Icon, Tooltip} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from 'src/JobTick';
import {JobRunStatus} from 'src/JobUtils';
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
    <div style={{width: 300}}>
      <p>The status of each partition in the partition set associated with this sensor.</p>
      <p>
        Partitions have a `Success` status if the last run for that partition completed
        successfully.
      </p>
      <p>Partititons have a `Missing` status if no run has been executed for that partition.</p>
    </div>
  );
  return (
    <>
      <Table striped style={{width: '100%'}}>
        <thead>
          <tr>
            <th style={{width: '60px'}}></th>
            <th>Sensor Name</th>
            <th>Pipeline</th>
            <th style={{width: '150px'}}>Frequency</th>
            <th style={{width: '120px'}}>
              <Box flex={{direction: 'row', alignItems: 'center'}}>
                Last Tick
                <Tooltip position={'right'} content={lastTick} wrapperTagName="div">
                  <Icon icon={IconNames.INFO_SIGN} style={{marginLeft: 10}} iconSize={15} />
                </Tooltip>
              </Box>
            </th>
            <th>
              <Box flex={{direction: 'row', alignItems: 'center'}}>
                Last Run
                <Tooltip position={'right'} content={lastRun} wrapperTagName="div">
                  <Icon icon={IconNames.INFO_SIGN} style={{marginLeft: 10}} iconSize={15} />
                </Tooltip>
              </Box>
            </th>
            <th>
              <Box flex={{direction: 'row', alignItems: 'center'}}>
                Partition Set Status
                <Tooltip position={'right'} content={partitionStatus} wrapperTagName="div">
                  <Icon icon={IconNames.INFO_SIGN} style={{marginLeft: 10}} iconSize={15} />
                </Tooltip>
              </Box>
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
    </>
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
      <td style={{width: 60}}>
        <Switch
          disabled={toggleOnInFlight || toggleOffInFlight}
          large
          innerLabelChecked="on"
          innerLabel="off"
          checked={status === JobStatus.RUNNING}
          onChange={onChangeSwitch}
        />
      </td>
      <td>
        <Link to={workspacePathFromAddress(repoAddress, `/sensors/${name}`)}>{name}</Link>
      </td>
      <td>
        <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}`)}>
          {pipelineName}
        </Link>
      </td>
      <td style={{maxWidth: 150}}>~ 30 seconds</td>
      <td style={{maxWidth: 100}}>
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
      <td>&mdash;</td>
      <td>
        <div style={{display: 'flex', alignItems: 'center'}}>
          <div>{`Mode: ${mode}`}</div>
        </div>
      </td>
    </tr>
  );
};
