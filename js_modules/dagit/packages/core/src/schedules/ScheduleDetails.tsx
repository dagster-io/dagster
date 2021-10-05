import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {useCopyToClipboard} from '../app/browser';
import {TickTag} from '../instigation/InstigationTick';
import {RepositoryLink} from '../nav/RepositoryLink';
import {PipelineReference} from '../pipelines/PipelineReference';
import {InstigationStatus, InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {CountdownStatus, useCountdown} from '../ui/Countdown';
import {Group} from '../ui/Group';
import {MetadataTable} from '../ui/MetadataTable';
import {PageHeader} from '../ui/PageHeader';
import {RefreshableCountdown} from '../ui/RefreshableCountdown';
import {TagWIP} from '../ui/TagWIP';
import {Code, Heading, Mono} from '../ui/Text';
import {Tooltip} from '../ui/Tooltip';
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
  const {flagPipelineModeTuples} = useFeatureFlags();
  const copyToClipboard = useCopyToClipboard();

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
            <Tooltip content={copyText}>
              <ButtonLink
                color={{link: ColorsWIP.Gray400, hover: ColorsWIP.Gray600}}
                onClick={copyId}
              >
                <Mono>{`id: ${id.slice(0, 8)}`}</Mono>
              </ButtonLink>
            </Tooltip>
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
      <Box padding={{vertical: 16, horizontal: 24}}>
        <MetadataTable
          rows={[
            schedule.description
              ? {
                  key: 'Description',
                  value: schedule.description,
                }
              : null,
            {
              key: 'Latest tick',
              value: latestTick ? (
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
              ),
            },
            {
              key: flagPipelineModeTuples ? 'Job' : 'Pipeline',
              value: (
                <PipelineReference
                  pipelineName={pipelineName}
                  pipelineHrefContext={repoAddress}
                  mode={schedule.mode}
                />
              ),
            },
            {
              key: 'Partition Set',
              value: partitionSet ? (
                <SchedulePartitionStatus schedule={schedule} repoAddress={repoAddress} />
              ) : (
                'None'
              ),
            },
            {
              key: 'Schedule',
              value: cronSchedule ? (
                <Group direction="row" spacing={8}>
                  <span>{humanCronString(cronSchedule)}</span>
                  <Code>({cronSchedule})</Code>
                </Group>
              ) : (
                <div>&mdash;</div>
              ),
            },
            executionTimezone
              ? {
                  key: 'Execution timezone',
                  value: executionTimezone,
                }
              : null,
          ].filter(Boolean)}
        />
      </Box>
    </>
  );
};
