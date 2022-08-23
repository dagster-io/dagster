import {Body, Box, Colors, FontFamily, Table} from '@dagster-io/ui';
import * as React from 'react';

import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {LegacyPipelineTag} from '../pipelines/LegacyPipelineTag';
import {PipelineReference} from '../pipelines/PipelineReference';
import {makeJobKey} from '../runs/QueryfulRunTimeline';
import {RunStatusPezList} from '../runs/RunStatusPez';
import {RunTimeFragment} from '../runs/types/RunTimeFragment';
import {ScheduleSwitchFragment} from '../schedules/types/ScheduleSwitchFragment';
import {SensorSwitchFragment} from '../sensors/types/SensorSwitchFragment';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {JobMenu} from './JobMenu';
import {LastRunSummary} from './LastRunSummary';
import {NextTick} from './NextTick';
import {ScheduleFutureTicksFragment} from './types/ScheduleFutureTicksFragment';

export type ScheduleFragment = ScheduleSwitchFragment & ScheduleFutureTicksFragment;

export type JobItem = {
  name: string;
  isJob: boolean;
  repoAddress: RepoAddress;
  schedules: ScheduleFragment[];
  sensors: SensorSwitchFragment[];
};

export type JobItemWithRuns = JobItem & {
  runs: RunTimeFragment[];
};

interface Props {
  jobs: JobItemWithRuns[];
}

export const JobTable = (props: Props) => {
  const {jobs} = props;
  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '40%'}}>Job</th>
          <th style={{width: '25%'}}>Trigger</th>
          <th style={{width: '35%'}}>Latest run</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {jobs.map(({isJob, name, repoAddress, runs, schedules, sensors}) => {
          const jobKey = makeJobKey(repoAddress, name);
          const repoAddressString = repoAddressAsString(repoAddress);
          return (
            <tr key={jobKey}>
              <td>
                <Box
                  flex={{
                    direction: 'row',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                  }}
                >
                  <Box flex={{direction: 'column', gap: 4}}>
                    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                      <PipelineReference
                        pipelineName={name}
                        isJob={isJob}
                        pipelineHrefContext={repoAddress}
                      />
                      {!isJob ? <LegacyPipelineTag /> : null}
                    </Box>
                    <Body color={Colors.Gray400} style={{fontFamily: FontFamily.monospace}}>
                      {repoAddressString}
                    </Body>
                  </Box>
                  {runs.length ? (
                    <Box margin={{top: 4}}>
                      <RunStatusPezList fade runs={runs} repoAddress={repoAddressString} />
                    </Box>
                  ) : null}
                </Box>
              </td>
              <td>
                {schedules.length || sensors.length ? (
                  <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 8}}>
                    <ScheduleOrSensorTag
                      schedules={schedules}
                      sensors={sensors}
                      repoAddress={repoAddress}
                    />
                    {schedules.length ? <NextTick schedules={schedules} /> : null}
                  </Box>
                ) : (
                  <div style={{color: Colors.Gray500}}>None</div>
                )}
              </td>
              <td>
                {runs.length ? (
                  <LastRunSummary run={runs[0]} />
                ) : (
                  <div style={{color: Colors.Gray500}}>None</div>
                )}
              </td>
              <td>
                <JobMenu job={{isJob, name, runs}} repoAddress={repoAddress} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
};
