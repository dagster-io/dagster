import {useMutation} from '@apollo/client';
import {Colors, Icon, Tooltip} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from 'src/jobs/JobTick';
import {JobRunStatus} from 'src/jobs/JobUtils';
import {PipelineAndMode} from 'src/pipelines/PipelineAndMode';
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

  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '60px'}}></th>
          <th>Sensor Name</th>
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
          <span style={{fontWeight: 500}}>
            <Link to={workspacePathFromAddress(repoAddress, `/sensors/${name}`)}>{name}</Link>
          </span>
          <Group direction="row" spacing={4} alignItems="center">
            <Icon
              icon="diagram-tree"
              color={Colors.GRAY2}
              iconSize={9}
              style={{position: 'relative', top: '-3px'}}
            />
            <span style={{fontSize: '13px'}}>
              <PipelineAndMode
                pipelineName={pipelineName}
                pipelineHref={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/`)}
                mode={mode}
              />
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
    </tr>
  );
};
