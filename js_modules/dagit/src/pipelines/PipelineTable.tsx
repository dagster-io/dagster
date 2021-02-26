import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {PipelineTableFragment} from 'src/pipelines/types/PipelineTableFragment';
import {RunStatusWithStats} from 'src/runs/RunStatusDots';
import {Group} from 'src/ui/Group';
import {Table} from 'src/ui/Table';
import {Caption} from 'src/ui/Text';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

export type PipelineForTable = {pipeline: PipelineTableFragment; repoAddress: RepoAddress};

interface Props {
  pipelines: PipelineForTable[];
  showRepo: boolean;
}

export const PipelineTable: React.FC<Props> = (props) => {
  const {pipelines, showRepo} = props;

  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '50%', minWidth: '400px'}}>Pipeline</th>
          <th>Schedules</th>
          <th>Sensors</th>
          <th style={{whiteSpace: 'nowrap'}}>Recent runs</th>
        </tr>
      </thead>
      <tbody>
        {pipelines.map(({pipeline, repoAddress}) => (
          <tr key={`${pipeline.name}-${repoAddressAsString(repoAddress)}`}>
            <td>
              <Group direction="column" spacing={4}>
                <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipeline.name}`)}>
                  <span style={{fontWeight: 500}}>{pipeline.name}</span>
                </Link>
                {showRepo ? <Caption>{repoAddressAsString(repoAddress)}</Caption> : null}
                <Description>{pipeline.description}</Description>
              </Group>
            </td>
            <td>
              {pipeline.schedules?.length ? (
                <Group direction="column" spacing={2}>
                  {pipeline.schedules.map((schedule) => (
                    <Link
                      key={schedule.name}
                      to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}
                    >
                      {schedule.name}
                    </Link>
                  ))}
                </Group>
              ) : (
                <div style={{color: Colors.GRAY5}}>None</div>
              )}
            </td>
            <td>
              {pipeline.sensors?.length ? (
                <Group direction="column" spacing={2}>
                  {pipeline.sensors.map((sensor) => (
                    <Link
                      key={sensor.name}
                      to={workspacePathFromAddress(repoAddress, `/sensors/${sensor.name}`)}
                    >
                      {sensor.name}
                    </Link>
                  ))}
                </Group>
              ) : (
                <div style={{color: Colors.GRAY5}}>None</div>
              )}
            </td>
            <td>
              <Group direction="row" spacing={4} alignItems="center">
                {pipeline.runs.map((run) => (
                  <RunStatusWithStats
                    key={run.runId}
                    runId={run.runId}
                    status={run.status}
                    size={12}
                  />
                ))}
              </Group>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};

const Description = styled.div`
  color: ${Colors.GRAY3};
  font-size: 12px;
`;

export const PIPELINE_TABLE_FRAGMENT = gql`
  fragment PipelineTableFragment on Pipeline {
    id
    description
    name
    runs(limit: 5) {
      id
      runId
      status
    }
    schedules {
      id
      name
    }
    sensors {
      id
      name
    }
  }
`;
