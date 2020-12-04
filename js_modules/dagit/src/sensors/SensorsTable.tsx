import {useMutation} from '@apollo/client';
import {Colors, Switch, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {RunStatus} from 'src/runs/RunStatusDots';
import {titleForRun} from 'src/runs/RunUtils';
import {TickTag} from 'src/schedules/ScheduleRow';
import {
  displaySensorMutationErrors,
  START_SENSOR_MUTATION,
  STOP_SENSOR_MUTATION,
} from 'src/sensors/SensorMutations';
import {SensorFragment} from 'src/sensors/types/SensorFragment';
import {StartSensor} from 'src/sensors/types/StartSensor';
import {StopSensor} from 'src/sensors/types/StopSensor';
import {JobStatus} from 'src/types/globalTypes';
import {Table} from 'src/ui/Table';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface RowProps {
  repoAddress: RepoAddress;
  sensor: SensorFragment;
}

const SensorRow = (props: RowProps) => {
  const {repoAddress, sensor} = props;
  const {
    name,
    pipelineName,
    sensorState: {runs, status, ticks},
  } = sensor;
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
      <td>
        {latestTick ? (
          <TickTag status={latestTick.status} eventSpecificData={null} />
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
        )}
      </td>
      <td>
        <div style={{display: 'flex'}}>
          {runs.length ? (
            runs.map((run) => {
              return (
                <div
                  style={{
                    cursor: 'pointer',
                    marginRight: '4px',
                  }}
                  key={run.runId}
                >
                  <Link to={`/instance/runs/${run.runId}`}>
                    <Tooltip
                      position={'top'}
                      content={titleForRun(run)}
                      wrapperTagName="div"
                      targetTagName="div"
                    >
                      <RunStatus status={run.status} />
                    </Tooltip>
                  </Link>
                </div>
              );
            })
          ) : (
            <span style={{color: Colors.GRAY4}}>None</span>
          )}
        </div>
      </td>
    </tr>
  );
};

interface Props {
  repoAddress: RepoAddress;
  sensors: SensorFragment[];
}

export const SensorsTable = (props: Props) => {
  const {repoAddress, sensors} = props;

  return (
    <>
      <Table striped style={{width: '100%'}}>
        <thead>
          <tr>
            <th style={{width: '60px'}}></th>
            <th>Sensor Name</th>
            <th>Pipeline</th>
            <th style={{width: '100px'}}>Last Tick</th>
            <th>Latest runs</th>
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
