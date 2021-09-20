import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {Group} from '../ui/Group';
import {Table} from '../ui/Table';
import {Caption} from '../ui/Text';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {PipelineReference} from './PipelineReference';
import {PipelineTableFragment} from './types/PipelineTableFragment';

type PipelineForTable = {pipeline: PipelineTableFragment; repoAddress: RepoAddress; mode?: string};

interface Props {
  pipelines: PipelineForTable[];
  showRepo: boolean;
}

export const PipelineTable: React.FC<Props> = (props) => {
  const {pipelines, showRepo} = props;
  const {flagPipelineModeTuples} = useFeatureFlags();

  let items = pipelines;
  if (flagPipelineModeTuples) {
    items = [];
    for (const item of pipelines) {
      items.push(...item.pipeline.modes.map((mode) => ({...item, mode: mode.name})));
    }
  }

  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '50%', minWidth: '400px'}}>
            {flagPipelineModeTuples ? 'Job' : 'Pipeline'}
          </th>
          <th>Schedules</th>
          <th>Sensors</th>
          <th style={{whiteSpace: 'nowrap'}}>Recent runs</th>
        </tr>
      </thead>
      <tbody>
        {items.map(({pipeline, repoAddress, mode}) => (
          <tr key={`${pipeline.name}-${repoAddressAsString(repoAddress)}`}>
            <td>
              <Group direction="column" spacing={4}>
                <PipelineReference
                  pipelineName={pipeline.name}
                  mode={mode || pipeline.modes[0].name}
                  pipelineHrefContext={repoAddress}
                />
                {showRepo ? <Caption>{repoAddressAsString(repoAddress)}</Caption> : null}
                <Description>{pipeline.description}</Description>
              </Group>
            </td>
            <td>
              {pipeline.schedules?.length ? (
                <Group direction="column" spacing={2}>
                  {pipeline.schedules
                    .filter((s) => !mode || s.mode === mode)
                    .map((schedule) => (
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
                  {pipeline.sensors
                    .filter(
                      (s) =>
                        !mode ||
                        s.targets?.some(
                          (target) =>
                            target.mode === mode && target?.pipelineName === pipeline.name,
                        ),
                    )
                    .map((sensor) => (
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
  color: ${Colors.GRAY3};
  font-size: 12px;
`;

export const PIPELINE_TABLE_FRAGMENT = gql`
  fragment PipelineTableFragment on Pipeline {
    id
    description
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
