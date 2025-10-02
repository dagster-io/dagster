import {
  Box,
  Code,
  Group,
  MetadataTableWIP,
  PageHeader,
  Subtitle1,
  Tag,
} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import {ScheduleAlertDetails} from 'shared/schedules/ScheduleAlertDetails.oss';
import styled from 'styled-components';

import {SchedulePartitionStatus} from './SchedulePartitionStatus';
import {ScheduleResetButton} from './ScheduleResetButton';
import {ScheduleSwitch} from './ScheduleSwitch';
import {TimestampDisplay} from './TimestampDisplay';
import {humanCronString} from './humanCronString';
import {ScheduleFragment} from './types/ScheduleUtils.types';
import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {AutomationTargetList} from '../automation/AutomationTargetList';
import {AutomationAssetSelectionFragment} from '../automation/types/AutomationAssetSelectionFragment.types';
import {InstigationStatus} from '../graphql/types';
import {RepositoryLink} from '../nav/RepositoryLink';
import {DefinitionOwners} from '../owners/DefinitionOwners';
import {EvaluateTickButtonSchedule} from '../ticks/EvaluateTickButtonSchedule';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {RepoAddress} from '../workspace/types';

const TIME_FORMAT = {showSeconds: true, showTimezone: true};

export const ScheduleDetails = (props: {
  schedule: ScheduleFragment;
  repoAddress: RepoAddress;
  refreshState: QueryRefreshState;
  assetSelection: AutomationAssetSelectionFragment | null;
}) => {
  const {repoAddress, schedule, refreshState, assetSelection} = props;
  const {cronSchedule, executionTimezone, futureTicks, name, partitionSet, pipelineName} = schedule;
  const {scheduleState} = schedule;
  const {status, ticks} = scheduleState;
  const latestTick = ticks.length > 0 ? ticks[0] : null;
  const running = status === InstigationStatus.RUNNING;

  return (
    <>
      <PageHeader
        title={
          <Subtitle1 style={{display: 'flex', flexDirection: 'row', gap: 4}}>
            <Link to="/automation">Automation</Link>
            <span>/</span>
            {name}
          </Subtitle1>
        }
        tags={
          <Tag icon="schedule">
            Schedule in <RepositoryLink repoAddress={repoAddress} />
          </Tag>
        }
        right={
          <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
            <QueryRefreshCountdown refreshState={refreshState} />
            <EvaluateTickButtonSchedule
              name={schedule.name}
              repoAddress={repoAddress}
              jobName={pipelineName}
            />
          </Box>
        }
      />
      <MetadataTableWIP>
        <tbody>
          {schedule.description ? (
            <tr>
              <td>Description</td>
              <td>{schedule.description}</td>
            </tr>
          ) : null}
          {schedule.owners.length > 0 && (
            <tr>
              <td>Owners</td>
              <td>
                <DefinitionOwners owners={schedule.owners} />
              </td>
            </tr>
          )}
          <tr>
            <td>Latest tick</td>
            <td>
              {latestTick ? (
                <Group direction="row" spacing={8} alignItems="center">
                  <TimestampDisplay
                    timestamp={latestTick.timestamp}
                    timezone={executionTimezone}
                    timeFormat={TIME_FORMAT}
                  />
                  <TickStatusTag tick={latestTick} tickResultType="runs" />
                </Group>
              ) : (
                'Schedule has never run'
              )}
            </td>
          </tr>
          {futureTicks.results[0] && running && (
            <tr>
              <td>Next tick</td>
              <td>
                <TimestampDisplay
                  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                  timestamp={futureTicks.results[0].timestamp!}
                  timezone={executionTimezone}
                  timeFormat={TIME_FORMAT}
                />
              </td>
            </tr>
          )}
          {schedule.pipelineName || assetSelection ? (
            <tr>
              <td>Target</td>
              <TargetCell>
                <AutomationTargetList
                  targets={schedule.pipelineName ? [{pipelineName: schedule.pipelineName}] : null}
                  repoAddress={repoAddress}
                  assetSelection={assetSelection || null}
                  automationType="schedule"
                />
              </TargetCell>
            </tr>
          ) : null}
          <tr>
            <td>
              <Box flex={{alignItems: 'center'}} style={{height: '32px'}}>
                Running
              </Box>
            </td>
            <td>
              <Box
                flex={{direction: 'row', gap: 12, alignItems: 'center'}}
                style={{height: '32px'}}
              >
                <ScheduleSwitch repoAddress={repoAddress} schedule={schedule} />
                {schedule.canReset && (
                  <ScheduleResetButton repoAddress={repoAddress} schedule={schedule} />
                )}
              </Box>
            </td>
          </tr>
          <tr>
            <td>Partition set</td>
            <td>
              {partitionSet ? (
                <SchedulePartitionStatus schedule={schedule} repoAddress={repoAddress} />
              ) : (
                'None'
              )}
            </td>
          </tr>
          <tr>
            <td>Schedule</td>
            <td>
              {cronSchedule ? (
                <Group direction="row" spacing={8}>
                  <span>
                    {humanCronString(cronSchedule, {
                      longTimezoneName: executionTimezone || 'UTC',
                    })}
                  </span>
                  <Code>({cronSchedule})</Code>
                </Group>
              ) : (
                <div>&mdash;</div>
              )}
            </td>
          </tr>
          {executionTimezone ? (
            <tr>
              <td>Execution timezone</td>
              <td>{executionTimezone}</td>
            </tr>
          ) : null}
          <ScheduleAlertDetails repoAddress={repoAddress} scheduleName={name} />
        </tbody>
      </MetadataTableWIP>
    </>
  );
};

const TargetCell = styled.td`
  button {
    line-height: 20px;
  }
`;
