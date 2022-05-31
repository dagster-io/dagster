import {Box, Colors, Icon, Table, Tooltip} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {AssetLink} from '../assets/AssetLink';
import {TickTag} from '../instigation/InstigationTick';
import {InstigatedRunStatus} from '../instigation/InstigationUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {InstigationType} from '../types/globalTypes';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
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
          <th style={{width: '15%'}}>Frequency</th>
          <th style={{width: '10%'}}>
            <Box flex={{gap: 8, alignItems: 'end'}}>
              Last tick
              <Tooltip position="top" content={lastTick}>
                <Icon name="info" color={Colors.Gray500} />
              </Tooltip>
            </Box>
          </th>
          <th style={{width: '25%'}}>
            <Box flex={{gap: 8, alignItems: 'end'}}>
              Last Run
              <Tooltip position="top" content={lastRun}>
                <Icon name="info" color={Colors.Gray500} />
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
  const repo = useRepository(repoAddress);
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
                  key={target.pipelineName}
                  showIcon
                  size="small"
                  pipelineName={target.pipelineName}
                  pipelineHrefContext={repoAddress}
                  isJob={!!(repo && isThisThingAJob(repo, target.pipelineName))}
                />
              ))}
            </Box>
          ) : null}
          {sensor.metadata.assetKeys && sensor.metadata.assetKeys.length ? (
            <Box flex={{direction: 'column', gap: 2}}>
              {sensor.metadata.assetKeys.map((key) => (
                <AssetLink key={key.path.join('/')} path={key.path} icon="asset" />
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
          <span style={{color: Colors.Gray300}}>None</span>
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
