import {
  Box,
  ButtonLink,
  ColorsWIP,
  CountdownStatus,
  useCountdown,
  Group,
  MetadataTableWIP,
  PageHeader,
  RefreshableCountdown,
  TagWIP,
  Code,
  Heading,
  Mono,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';

import {useCopyToClipboard} from '../app/browser';
import {TickTag} from '../instigation/InstigationTick';
import {RepositoryLink} from '../nav/RepositoryLink';
import {PipelineReference} from '../pipelines/PipelineReference';
import {InstigationStatus, InstigationType} from '../types/globalTypes';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {SchedulePartitionStatus} from './SchedulePartitionStatus';
import {ScheduleSwitch} from './ScheduleSwitch';
import {TimestampDisplay} from './TimestampDisplay';
import {humanCronString} from './humanCronString';
import {ScheduleFragment} from './types/ScheduleFragment';

const TIME_FORMAT = {showSeconds: false, showTimezone: true};

export const ScheduleDetails: React.FC<{
  schedule: ScheduleFragment;
  repoAddress: RepoAddress;
  countdownDuration: number;
  countdownStatus: CountdownStatus;
  onRefresh: () => void;
}> = (props) => {
  const {repoAddress, schedule, countdownDuration, countdownStatus, onRefresh} = props;
  const {cronSchedule, executionTimezone, futureTicks, name, partitionSet, pipelineName} = schedule;
  const copyToClipboard = useCopyToClipboard();

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  const [copyText, setCopyText] = React.useState('Click to copy');

  const timeRemaining = useCountdown({
    duration: countdownDuration,
    status: countdownStatus,
  });

  // Restore the tooltip text after a delay.
  React.useEffect(() => {
    let token: any;
    if (copyText === 'Copied!') {
      token = setTimeout(() => {
        setCopyText('Click to copy');
      }, 2000);
    }
    return () => {
      token && clearTimeout(token);
    };
  }, [copyText]);

  const {scheduleState} = schedule;
  const {status, id, ticks} = scheduleState;
  const latestTick = ticks.length > 0 ? ticks[0] : null;

  const copyId = () => {
    copyToClipboard(id);
    setCopyText('Copied!');
  };

  const running = status === InstigationStatus.RUNNING;
  const countdownRefreshing = countdownStatus === 'idle' || timeRemaining === 0;
  const seconds = Math.floor(timeRemaining / 1000);

  return (
    <>
      <PageHeader
        title={
          <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
            <Heading>{name}</Heading>
            <ScheduleSwitch repoAddress={repoAddress} schedule={schedule} />
          </Box>
        }
        tags={
          <>
            <TagWIP icon="schedule">
              Schedule in <RepositoryLink repoAddress={repoAddress} />
            </TagWIP>
            {futureTicks.results.length && running ? (
              <TagWIP icon="timer">
                Next tick:{' '}
                <TimestampDisplay
                  timestamp={futureTicks.results[0].timestamp}
                  timezone={executionTimezone}
                  timeFormat={TIME_FORMAT}
                />
              </TagWIP>
            ) : null}
            <Box flex={{display: 'inline-flex'}} margin={{top: 2}}>
              <Tooltip content={copyText}>
                <ButtonLink
                  color={{link: ColorsWIP.Gray400, hover: ColorsWIP.Gray600}}
                  onClick={copyId}
                >
                  <Mono>{`id: ${id.slice(0, 8)}`}</Mono>
                </ButtonLink>
              </Tooltip>
            </Box>
          </>
        }
        right={
          <RefreshableCountdown
            refreshing={countdownRefreshing}
            seconds={seconds}
            onRefresh={onRefresh}
          />
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
                  <TickTag tick={latestTick} instigationType={InstigationType.SCHEDULE} />
                </Group>
              ) : (
                'Schedule has never run'
              )}
            </td>
          </tr>
          <tr>
            <td>{isJob ? 'Job' : 'Pipeline'}</td>
            <td>
              <PipelineReference
                pipelineName={pipelineName}
                pipelineHrefContext={repoAddress}
                isJob={isJob}
              />
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
                  <span>{humanCronString(cronSchedule)}</span>
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
        </tbody>
      </MetadataTableWIP>
    </>
  );
};
