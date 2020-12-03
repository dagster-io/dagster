import {useMutation} from '@apollo/client';
import {Button, Callout, Intent, Colors, Switch, Tooltip} from '@blueprintjs/core';
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
import {JobStateFragment} from 'src/sensors/types/JobStateFragment';
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

export const SensorStateRow = ({sensorState}: {sensorState: JobStateFragment}) => {
  const {id, name, status, runs, ticks} = sensorState;

  const [stopSensor, {loading: toggleOffInFlight}] = useMutation<StopSensor>(STOP_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });

  const onChangeSwitch = () => {
    if (status === JobStatus.RUNNING) {
      stopSensor({variables: {jobOriginId: id}});
    }
  };

  const latestTick = ticks.length ? ticks[0] : null;

  return (
    <tr key={name}>
      <td style={{width: 60}}>
        <Switch
          disabled={toggleOffInFlight || status === JobStatus.STOPPED}
          large
          innerLabelChecked="on"
          innerLabel="off"
          checked={status === JobStatus.RUNNING}
          onChange={onChangeSwitch}
        />
      </td>
      <td>{name}</td>
      <td></td>
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

export const UnloadableSensors: React.FunctionComponent<{
  sensorStates: JobStateFragment[];
}> = ({sensorStates}) => {
  return (
    <>
      <h3 style={{marginTop: 20}}>Unloadable sensors:</h3>
      <UnloadableSensorInfo />

      <Table striped style={{width: '100%'}}>
        <thead>
          <tr>
            <th style={{maxWidth: '60px'}}></th>
            <th>Sensor Name</th>
            <th></th>
            <th style={{width: '100px'}}>Last Tick</th>
            <th>Latest Runs</th>
          </tr>
        </thead>
        <tbody>
          {sensorStates.map((sensorState) => (
            <SensorStateRow sensorState={sensorState} key={sensorState.id} />
          ))}
        </tbody>
      </Table>
    </>
  );
};

export const UnloadableSensorInfo = () => {
  const [showMore, setShowMore] = React.useState(false);

  return (
    <Callout style={{marginBottom: 20}} intent={Intent.WARNING}>
      <div style={{display: 'flex', justifyContent: 'space-between'}}>
        <h4 style={{margin: 0}}>
          Note: You can turn off any of the following sensors, but you cannot turn them back on.{' '}
        </h4>

        {!showMore && (
          <Button small={true} onClick={() => setShowMore(true)}>
            Show more info
          </Button>
        )}
      </div>

      {showMore && (
        <div style={{marginTop: 10}}>
          <p>
            The following sensors were previously started but now cannot be loaded. They may be part
            of a different workspace or from a sensor or repository that no longer exists in code.
            You can turn them off, but you cannot turn them back on since they can’t be loaded.
          </p>
        </div>
      )}
    </Callout>
  );
};

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
