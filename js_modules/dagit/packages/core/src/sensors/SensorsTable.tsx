import {Colors, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from '../instigation/InstigationTick';
import {InstigatedRunStatus} from '../instigation/InstigationUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {InstigationType} from '../types/globalTypes';
import {Group} from '../ui/Group';
import {Table} from '../ui/Table';
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
  const {ticks} = sensorState;
  const latestTick = ticks.length ? ticks[0] : null;

  return (
    <tr key={name}>
      <td>
        <SensorSwitch repoAddress={repoAddress} sensor={sensor} />
      </td>
      <td>
        <Group direction="column" spacing={4}>
          <span style={{fontWeight: 500}}>
            <Link to={workspacePathFromAddress(repoAddress, `/sensors/${name}`)}>{name}</Link>
          </span>
          {pipelineName && mode !== null && (
            <PipelineReference
              showIcon
              fontSize={13}
              pipelineName={pipelineName}
              pipelineHrefContext={repoAddress}
              mode={mode}
            />
          )}
        </Group>
      </td>
      <td>{humanizeSensorInterval(sensor.minIntervalSeconds)}</td>
      <td>
        {latestTick ? (
          <TickTag tick={latestTick} instigationType={InstigationType.SENSOR} />
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
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
