import {gql} from '@apollo/client';
import {Colors, Group, Table, Caption} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {RunStatusWithStats} from '../runs/RunStatusDots';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {PipelineReference} from './PipelineReference';
import {PipelineTableFragment} from './types/PipelineTableFragment';

type PipelineForTable = {
  pipelineOrJob: PipelineTableFragment;
  repoAddress: RepoAddress;
};

interface Props {
  pipelinesOrJobs: PipelineForTable[];
  showRepo: boolean;
}

export const PipelineTable: React.FC<Props> = (props) => {
  const {pipelinesOrJobs, showRepo} = props;

  const anyPipelines = pipelinesOrJobs.some(({pipelineOrJob}) => !pipelineOrJob.isJob);

  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '50%', minWidth: '400px'}}>
            {anyPipelines ? 'Job or Pipeline' : 'Job'}
          </th>
          <th>Schedules</th>
          <th>Sensors</th>
          <th style={{whiteSpace: 'nowrap'}}>Recent runs</th>
        </tr>
      </thead>
      <tbody>
        {pipelinesOrJobs.map(({pipelineOrJob, repoAddress}) => (
          <tr key={`${pipelineOrJob.name}-${repoAddressAsString(repoAddress)}`}>
            <td>
              <Group direction="column" spacing={4}>
                <PipelineReference
                  isJob={pipelineOrJob.isJob}
                  pipelineName={pipelineOrJob.name}
                  pipelineHrefContext={repoAddress}
                  truncationThreshold={80}
                />
                {showRepo ? <Caption>{repoAddressAsString(repoAddress)}</Caption> : null}
                <Description>{pipelineOrJob.description}</Description>
              </Group>
            </td>
            <td>
              {pipelineOrJob.schedules?.length ? (
                <Group direction="column" spacing={2}>
                  {pipelineOrJob.schedules.map((schedule) => (
                    <Link
                      key={schedule.name}
                      to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}
                    >
                      {schedule.name}
                    </Link>
                  ))}
                </Group>
              ) : (
                <div style={{color: Colors.Gray200}}>None</div>
              )}
            </td>
            <td>
              {pipelineOrJob.sensors?.length ? (
                <Group direction="column" spacing={2}>
                  {pipelineOrJob.sensors.map((sensor) => (
                    <Link
                      key={sensor.name}
                      to={workspacePathFromAddress(repoAddress, `/sensors/${sensor.name}`)}
                    >
                      {sensor.name}
                    </Link>
                  ))}
                </Group>
              ) : (
                <div style={{color: Colors.Gray200}}>None</div>
              )}
            </td>
            <td>
              <Group direction="row" spacing={4} alignItems="center">
                {pipelineOrJob.runs.map((run) => (
                  <RunStatusWithStats
                    key={run.id}
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
  color: ${Colors.Gray400};
  font-size: 12px;
`;

export const PIPELINE_TABLE_FRAGMENT = gql`
  fragment PipelineTableFragment on Pipeline {
    id
    description
    isJob
    name
    modes {
      id
      name
    }
    runs(limit: 5) {
      id
      mode
      runId
      status
    }
    schedules {
      id
      name
      mode
    }
    sensors {
      id
      name
      targets {
        mode
        pipelineName
      }
    }
  }
`;
