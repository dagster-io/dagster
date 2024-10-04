import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  ExternalAnchorButton,
  Group,
  Icon,
  Menu,
  MenuItem,
  NonIdealState,
  Popover,
  Spinner,
  StyledRawCodeMirror,
  Subheading,
  Table,
} from '@dagster-io/ui-components';
import qs from 'qs';
import {memo, useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {TimestampDisplay} from './TimestampDisplay';
import {
  RepositoryForNextTicksFragment,
  ScheduleFutureTickEvaluationResultFragment,
  ScheduleFutureTickRunRequestFragment,
  ScheduleNextFiveTicksFragment,
  ScheduleTickConfigQuery,
  ScheduleTickConfigQueryVariables,
} from './types/SchedulesNextTicks.types';
import {gql, useLazyQuery} from '../apollo-client';
import {showSharedToaster} from '../app/DomUtils';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {useCopyToClipboard} from '../app/browser';
import {InstigationStatus} from '../graphql/types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RunTags} from '../runs/RunTags';
import {MenuLink} from '../ui/MenuLink';
import {
  findRepositoryAmongOptions,
  isThisThingAJob,
  useRepository,
  useRepositoryOptions,
} from '../workspace/WorkspaceContext/util';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface ScheduleTick {
  schedule: ScheduleNextFiveTicksFragment;
  timestamp: number;
  repoAddress: RepoAddress;
}

interface Props {
  repos: RepositoryForNextTicksFragment[];
}

export const SchedulesNextTicks = memo(({repos}: Props) => {
  const nextTicks: ScheduleTick[] = [];
  let anyPipelines = false;
  let anySchedules = false;

  const {options} = useRepositoryOptions();

  repos.forEach((repo) => {
    const {schedules} = repo;
    anySchedules = anySchedules || schedules.length > 0;

    const repoAddress = {
      name: repo.name,
      location: repo.location.name,
    };

    const futureTickSchedules = schedules.filter(
      (schedule) =>
        schedule.futureTicks.results.length &&
        schedule.scheduleState.status === InstigationStatus.RUNNING,
    );

    const minMaxTimestamp = Math.min(
      ...futureTickSchedules.map(
        (schedule) =>
          schedule.futureTicks.results[schedule.futureTicks.results.length - 1]!.timestamp!,
      ),
    );

    futureTickSchedules.forEach((schedule) => {
      schedule.futureTicks.results.forEach((tick) => {
        if (tick.timestamp! <= minMaxTimestamp) {
          nextTicks.push({schedule, timestamp: tick.timestamp!, repoAddress});
        }
      });
    });

    if (!anyPipelines) {
      anyPipelines = schedules.some((schedule) => !!schedule.mode);
    }
  });

  nextTicks.sort((a, b) => a.timestamp - b.timestamp);

  if (!nextTicks.length) {
    return (
      <Box padding={{vertical: 32}}>
        <NonIdealState
          icon="error"
          title="No scheduled ticks"
          description={
            anySchedules ? (
              <>
                There are no running schedules.{' '}
                <Link to="/overview/schedules">Start a schedule</Link> to see scheduled ticks.
              </>
            ) : (
              <>
                There are no schedules in this workspace. Create a running schedule to view its
                scheduled ticks.
              </>
            )
          }
          action={
            anySchedules ? null : (
              <ExternalAnchorButton
                icon={<Icon name="open_in_new" />}
                href="https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules"
              >
                View documentation
              </ExternalAnchorButton>
            )
          }
        />
      </Box>
    );
  }

  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '260px'}}>Timestamp</th>
          <th style={{width: '30%'}}>Schedule</th>
          <th>{anyPipelines ? 'Job / Pipeline' : 'Job'}</th>
          <th>Metadata</th>
        </tr>
      </thead>
      <tbody>
        {nextTicks.map(({schedule, timestamp, repoAddress}) => {
          const repo = findRepositoryAmongOptions(options, repoAddress);
          return (
            <tr key={`${schedule.id}:${timestamp}`}>
              <td>
                <TimestampDisplay
                  timestamp={timestamp}
                  timezone={schedule.executionTimezone}
                  timeFormat={{showSeconds: false, showTimezone: true}}
                />
              </td>
              <td>
                <Link to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}>
                  {schedule.name}
                </Link>
              </td>
              <td>
                <PipelineReference
                  pipelineName={schedule.pipelineName}
                  pipelineHrefContext={repoAddress}
                  isJob={!!repo && isThisThingAJob(repo, schedule.pipelineName)}
                />
              </td>
              <td>
                <NextTickMenu
                  repoAddress={repoAddress}
                  schedule={schedule}
                  tickTimestamp={timestamp}
                />
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
});

interface NextTickMenuProps {
  repoAddress: RepoAddress;
  schedule: ScheduleNextFiveTicksFragment;
  tickTimestamp: number;
}

const NextTickMenu = memo(({repoAddress, schedule, tickTimestamp}: NextTickMenuProps) => {
  const scheduleSelector = {
    ...repoAddressToSelector(repoAddress),
    scheduleName: schedule.name,
  };
  const [isOpen, setOpen] = useState<boolean>(false);
  const [loadTickConfig, {called, loading, data}] = useLazyQuery<
    ScheduleTickConfigQuery,
    ScheduleTickConfigQueryVariables
  >(SCHEDULE_TICK_CONFIG_QUERY, {
    variables: {
      scheduleSelector,
      tickTimestamp,
    },
  });

  const infoReady = called ? !loading : false;
  const evaluationResult =
    data?.scheduleOrError?.__typename === 'Schedule'
      ? data.scheduleOrError.futureTick.evaluationResult
      : null;

  const menuItems = infoReady ? (
    <NextTickMenuItems
      repoAddress={repoAddress}
      schedule={schedule}
      loading={loading}
      onItemOpen={setOpen}
      evaluationResult={evaluationResult}
    />
  ) : (
    <Spinner purpose="body-text" />
  );
  return (
    <>
      <Popover
        content={<Menu>{menuItems}</Menu>}
        position="bottom-right"
        onOpening={() => {
          if (!called) {
            loadTickConfig();
          }
        }}
      >
        <Button icon={<Icon name="expand_more" />} />
      </Popover>
      <NextTickDialog
        repoAddress={repoAddress}
        isOpen={isOpen}
        setOpen={setOpen}
        schedule={schedule}
        tickTimestamp={tickTimestamp}
        evaluationResult={evaluationResult}
      />
    </>
  );
});

const NextTickMenuItems = ({
  repoAddress,
  schedule,
  evaluationResult,
  loading,
  onItemOpen,
}: {
  repoAddress: RepoAddress;
  evaluationResult: ScheduleFutureTickEvaluationResultFragment | null;
  schedule: ScheduleNextFiveTicksFragment;
  loading: boolean;
  onItemOpen: (value: boolean) => void;
}) => {
  if (!evaluationResult) {
    return <MenuItem text="Could not preview tick for this schedule" />;
  }

  if (evaluationResult.skipReason) {
    return <MenuItem text="View skip reason..." onClick={() => onItemOpen(true)} />;
  }

  if (evaluationResult.error) {
    return <MenuItem text="View error..." onClick={() => onItemOpen(true)} />;
  }

  if (!evaluationResult.runRequests || !evaluationResult.runRequests.length) {
    return <MenuItem text="No runs requested for this projected schedule tick" />;
  }

  if (evaluationResult.runRequests.length === 1) {
    const runRequest = evaluationResult.runRequests[0];
    const runConfigYaml = runRequest ? runRequest.runConfigYaml : '';
    return (
      <>
        <MenuItem
          text={loading ? 'Loading Configuration...' : 'View Configuration...'}
          icon="open_in_new"
          onClick={() => onItemOpen(true)}
        />
        <MenuLink
          text="Open in Launchpad..."
          icon="edit"
          target="_blank"
          to={workspacePathFromAddress(
            repoAddress,
            `/pipeline_or_job/${schedule.pipelineName}/playground/setup?${qs.stringify({
              mode: schedule.mode,
              config: runConfigYaml,
              solidSelection: schedule.solidSelection,
            })}`,
          )}
        />
      </>
    );
  }

  return (
    <MenuItem
      text={`View ${evaluationResult.runRequests.length} run requests...`}
      icon="edit"
      target="_blank"
      onClick={() => onItemOpen(true)}
    />
  );
};

const NextTickDialog = ({
  repoAddress,
  evaluationResult,
  schedule,
  tickTimestamp,
  setOpen,
  isOpen,
}: {
  repoAddress: RepoAddress;
  isOpen: boolean;
  setOpen: (value: boolean) => void;
  evaluationResult: ScheduleFutureTickEvaluationResultFragment | null;
  schedule: ScheduleNextFiveTicksFragment;
  tickTimestamp: number;
}) => {
  const [selectedRunRequest, setSelectedRunRequest] =
    useState<ScheduleFutureTickRunRequestFragment | null>(
      evaluationResult && evaluationResult.runRequests && evaluationResult.runRequests.length === 1
        ? evaluationResult.runRequests[0]!
        : null,
    );

  const copy = useCopyToClipboard();

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, schedule.pipelineName);

  useEffect(() => {
    if (
      evaluationResult &&
      evaluationResult.runRequests &&
      evaluationResult.runRequests.length === 1
    ) {
      setSelectedRunRequest(evaluationResult.runRequests[0]!);
    }
  }, [evaluationResult]);

  const close = () => {
    setSelectedRunRequest(null);
    setOpen(false);
  };

  let body;
  if (!evaluationResult) {
    body = null;
  } else if (selectedRunRequest) {
    body = (
      <Box flex={{direction: 'column', gap: 20}}>
        <Box flex={{direction: 'column', gap: 12}} padding={{top: 16, horizontal: 24}}>
          <Subheading>Tags</Subheading>
          {selectedRunRequest.tags.length ? (
            <RunTags tags={selectedRunRequest.tags} mode={isJob ? null : schedule.mode} />
          ) : null}
        </Box>
        <div>
          <Box border="bottom" padding={{left: 24, bottom: 16}}>
            <Subheading>Config</Subheading>
          </Box>
          <StyledRawCodeMirror
            value={selectedRunRequest.runConfigYaml}
            options={{readOnly: true, lineNumbers: true, mode: 'yaml'}}
          />
        </div>
      </Box>
    );
  } else if (evaluationResult.error) {
    body = (
      <DialogBody>
        <PythonErrorInfo error={evaluationResult.error} />
      </DialogBody>
    );
  } else if (evaluationResult.skipReason) {
    body = (
      <DialogBody>
        <SkipWrapper>{evaluationResult.skipReason}</SkipWrapper>
      </DialogBody>
    );
  } else if (evaluationResult.runRequests) {
    body = (
      <DialogBody>
        <RunRequestBody>
          <Table>
            <thead>
              <tr>
                <th>Run key</th>
                <th>Config</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {evaluationResult.runRequests.map((runRequest, idx) => {
                if (!runRequest) {
                  return null;
                }
                return (
                  <tr key={idx}>
                    <td>{runRequest.runKey || <span>&mdash;</span>}</td>
                    <td>
                      <ButtonLink
                        onClick={() => setSelectedRunRequest(runRequest)}
                        underline="never"
                      >
                        <Group direction="row" spacing={8} alignItems="center">
                          <Icon name="open_in_new" color={Colors.textLight()} />
                          <span>View config</span>
                        </Group>
                      </ButtonLink>
                    </td>
                    <td>
                      <Popover
                        content={
                          <Menu>
                            <MenuLink
                              text="Open in Launchpad..."
                              icon="edit"
                              to={workspacePathFromAddress(
                                repoAddress,
                                `/${isJob ? 'jobs' : 'pipelines'}/${
                                  schedule.pipelineName
                                }/playground/setup?${qs.stringify({
                                  mode: schedule.mode,
                                  config: runRequest.runConfigYaml,
                                  solidSelection: schedule.solidSelection,
                                })}`,
                              )}
                            />
                          </Menu>
                        }
                        position="bottom"
                      >
                        <Button icon={<Icon name="expand_more" />} />
                      </Popover>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        </RunRequestBody>
      </DialogBody>
    );
  }

  return (
    <Dialog
      onClose={() => close()}
      style={{width: '50vw'}}
      title={
        <Box flex={{direction: 'row', gap: 4}}>
          <TimestampDisplay timestamp={tickTimestamp} timezone={schedule.executionTimezone} />
          {selectedRunRequest?.runKey ? <div>: {selectedRunRequest?.runKey}</div> : null}
        </Box>
      }
      isOpen={isOpen}
    >
      {body}
      <DialogFooter topBorder>
        {selectedRunRequest ? (
          <Button
            autoFocus={false}
            onClick={async () => {
              copy(selectedRunRequest.runConfigYaml);
              await showSharedToaster({
                intent: 'success',
                icon: 'copy_to_clipboard_done',
                message: 'Copied!',
              });
            }}
          >
            Copy config
          </Button>
        ) : null}
        <Button intent="primary" autoFocus={true} onClick={() => close()}>
          OK
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const SCHEDULE_NEXT_FIVE_TICKS_FRAGMENT = gql`
  fragment ScheduleNextFiveTicksFragment on Schedule {
    id
    name
    executionTimezone
    mode
    solidSelection
    pipelineName
    scheduleState {
      id
      status
    }
    futureTicks(limit: 5) {
      results {
        timestamp
      }
    }
  }
`;

export const REPOSITORY_FOR_NEXT_TICKS_FRAGMENT = gql`
  fragment RepositoryForNextTicksFragment on Repository {
    name
    id
    location {
      id
      name
    }
    schedules {
      id
      ...ScheduleNextFiveTicksFragment
    }
  }

  ${SCHEDULE_NEXT_FIVE_TICKS_FRAGMENT}
`;

const SCHEDULE_TICK_CONFIG_QUERY = gql`
  query ScheduleTickConfigQuery($scheduleSelector: ScheduleSelector!, $tickTimestamp: Int!) {
    scheduleOrError(scheduleSelector: $scheduleSelector) {
      ... on Schedule {
        id
        futureTick(tickTimestamp: $tickTimestamp) {
          evaluationResult {
            ...ScheduleFutureTickEvaluationResult
          }
        }
      }
    }
  }

  fragment ScheduleFutureTickEvaluationResult on TickEvaluation {
    runRequests {
      ...ScheduleFutureTickRunRequest
    }
    skipReason
    error {
      ...PythonErrorFragment
    }
  }

  fragment ScheduleFutureTickRunRequest on RunRequest {
    runKey
    runConfigYaml
    tags {
      key
      value
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

const RunRequestBody = styled.div`
  font-size: 13px;
`;

const SkipWrapper = styled.div`
  background-color: ${Colors.backgroundYellow()};
  border: 1px solid ${Colors.accentYellow()};
  border-radius: 3px;
`;
