import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from '../instigation/InstigationTick';
import {InstigatedRunStatus} from '../instigation/InstigationUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
import {Table} from '../ui/Table';
import {Tooltip} from '../ui/Tooltip';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {humanizeSensorInterval} from './SensorDetails';
import {SensorSwitch} from './SensorSwitch';
import {SensorFragment} from './types/SensorFragment';

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
            <Box flex={{gap: 8, alignItems: 'end'}}>
              Last tick
              <Tooltip position="top" content={lastTick}>
                <IconWIP name="info" color={ColorsWIP.Gray500} />
              </Tooltip>
            </Box>
          </th>
          <th>
            <Box flex={{gap: 8, alignItems: 'end'}}>
              Last Run
              <Tooltip position="top" content={lastRun}>
                <IconWIP name="info" color={ColorsWIP.Gray500} />
              </Tooltip>
            </Box>
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
  const {name, sensorState} = sensor;
  const {ticks} = sensorState;
  const latestTick = ticks.length ? ticks[0] : null;

  return (
    <tr key={name}>
      <td>
        <SensorSwitch repoAddress={repoAddress} sensor={sensor} />
      </td>
      <td>
        <Box flex={{direction: 'column', gap: 4}}>
          <span style={{fontWeight: 500}}>
            <Link to={workspacePathFromAddress(repoAddress, `/sensors/${name}`)}>{name}</Link>
          </span>
          {sensor.targets && sensor.targets.length ? (
            <Box flex={{direction: 'column', gap: 2}}>
              {sensor.targets.map((target) => (
                <PipelineReference
                  key={`${target.pipelineName}:${target.mode}`}
                  showIcon
                  size="small"
                  pipelineName={target.pipelineName}
                  pipelineHrefContext={repoAddress}
                  mode={target.mode}
                />
              ))}
            </Box>
          ) : null}
        </Box>
      </td>
      <td>{humanizeSensorInterval(sensor.minIntervalSeconds)}</td>
      <td>
        {latestTick ? (
          <TickTag tick={latestTick} instigationType={InstigationType.SENSOR} />
        ) : (
          <span style={{color: ColorsWIP.Gray300}}>None</span>
        )}
      </td>
      <td>
        <div style={{display: 'flex'}}>
          <InstigatedRunStatus instigationState={sensorState} />
        </div>
      </td>
    </tr>
  );
};
