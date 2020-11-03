import {useMutation, useQuery, gql} from '@apollo/client';
import {
  Button,
  Callout,
  Code,
  Colors,
  Icon,
  Intent,
  Menu,
  MenuItem,
  Popover,
  PopoverInteractionKind,
  Position,
  Spinner,
  Switch,
  Tag,
  Tooltip,
} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as qs from 'query-string';
import * as React from 'react';
import {useState} from 'react';
import {Link, useHistory, useRouteMatch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ButtonLink} from 'src/ButtonLink';
import {showCustomAlert} from 'src/CustomAlertProvider';
import {ConfirmationOptions, useConfirmation} from 'src/CustomConfirmationProvider';
import {
  DagsterRepoOption,
  repositorySelectorFromDagsterRepoOption,
  scheduleSelectorWithRepository,
  useCurrentRepositoryState,
  useRepositoryOptions,
  useScheduleSelector,
} from 'src/DagsterRepositoryContext';
import {HighlightedCodeBlock} from 'src/HighlightedCodeBlock';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {RepositoryOriginInformation} from 'src/RepositoryInformation';
import {assertUnreachable} from 'src/Util';
import {RunStatus} from 'src/runs/RunStatusDots';
import {titleForRun} from 'src/runs/RunUtils';
import {ReconcileButton} from 'src/schedules/ReconcileButton';
import {humanCronString} from 'src/schedules/humanCronString';
import {
  ScheduleDefinitionFragment,
  ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData,
} from 'src/schedules/types/ScheduleDefinitionFragment';
import {ScheduleStateFragment} from 'src/schedules/types/ScheduleStateFragment';
import {
  StartSchedule,
  StartSchedule_startSchedule_PythonError,
} from 'src/schedules/types/StartSchedule';
import {
  StopSchedule,
  StopSchedule_stopRunningSchedule_PythonError,
} from 'src/schedules/types/StopSchedule';
import {ScheduleStatus, ScheduleTickStatus} from 'src/types/globalTypes';
import {FontFamily} from 'src/ui/styles';

type TickSpecificData = ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData | null;

const NUM_RUNS_TO_DISPLAY = 10;

const errorDisplay = (status: ScheduleStatus, runningScheduleCount: number) => {
  if (status === ScheduleStatus.STOPPED && runningScheduleCount === 0) {
    return null;
  } else if (status === ScheduleStatus.RUNNING && runningScheduleCount === 1) {
    return null;
  }

  const errors = [];
  if (status === ScheduleStatus.RUNNING && runningScheduleCount === 0) {
    errors.push(
      'Schedule is set to be running, but either the scheduler is not configured or the scheduler is not running the schedule',
    );
  } else if (status === ScheduleStatus.STOPPED && runningScheduleCount > 0) {
    errors.push('Schedule is set to be stopped, but the scheduler is still running the schedule');
  }

  if (runningScheduleCount > 0) {
    errors.push('Duplicate cron job for schedule found.');
  }

  return (
    <Popover
      interactionKind={PopoverInteractionKind.CLICK}
      popoverClassName="bp3-popover-content-sizing"
      position={Position.RIGHT}
      fill={true}
    >
      <Tag fill={true} interactive={true} intent={Intent.DANGER}>
        Error
      </Tag>
      <div>
        <h3>There are errors with this schedule.</h3>

        <p>Errors:</p>
        <ul>
          {errors.map((error, index) => (
            <li key={index}>{error}</li>
          ))}
        </ul>

        <p>
          To resolve, click <ReconcileButton /> or run <Code>dagster schedule up</Code>
        </p>
      </div>
    </Popover>
  );
};

const displayScheduleMutationErrors = (data: StartSchedule | StopSchedule) => {
  let error:
    | StartSchedule_startSchedule_PythonError
    | StopSchedule_stopRunningSchedule_PythonError
    | null = null;

  if ('startSchedule' in data && data.startSchedule.__typename === 'PythonError') {
    error = data.startSchedule;
  } else if (
    'stopRunningSchedule' in data &&
    data.stopRunningSchedule.__typename === 'PythonError'
  ) {
    error = data.stopRunningSchedule;
  }

  if (error) {
    showCustomAlert({
      title: 'Schedule Response',
      body: (
        <>
          <PythonErrorInfo error={error} />
        </>
      ),
    });
  }
};

export const ScheduleRow: React.FunctionComponent<{
  schedule: ScheduleDefinitionFragment;
}> = ({schedule}) => {
  const match = useRouteMatch('/schedules/:scheduleName');

  const [startSchedule, {loading: toggleOnInFlight}] = useMutation(START_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });

  const {name, cronSchedule, pipelineName, mode, solidSelection, scheduleState} = schedule;

  const scheduleId = scheduleState?.scheduleOriginId;

  const scheduleSelector = useScheduleSelector(name);

  const [configRequested, setConfigRequested] = React.useState(false);

  const {data, loading: yamlLoading} = useQuery(FETCH_SCHEDULE_YAML, {
    variables: {scheduleSelector},
    skip: !configRequested,
  });

  const runConfigError =
    data?.scheduleDefinitionOrError?.runConfigOrError.__typename === 'PythonError'
      ? data.scheduleDefinitionOrError.runConfigOrError
      : null;

  const runConfigYaml = runConfigError
    ? null
    : data?.scheduleDefinitionOrError?.runConfigOrError.yaml;

  const displayName = match ? (
    <div>{name}</div>
  ) : (
    <>
      <div>
        <Link to={`/schedules/${name}`}>{name}</Link>
      </div>
      {scheduleId && (
        <span style={{fontSize: '12px'}}>
          Schedule ID: <span style={{fontFamily: FontFamily.monospace}}>{scheduleId}</span>
        </span>
      )}
    </>
  );

  if (!scheduleState) {
    return (
      <tr key={name}>
        <td>{displayName}</td>
        <td>
          <Link to={`/pipeline/${pipelineName}/`}>{pipelineName}</Link>
        </td>
        <td
          style={{
            maxWidth: 150,
          }}
        >
          {cronSchedule ? (
            <Tooltip position={'bottom'} content={cronSchedule}>
              {humanCronString(cronSchedule)}
            </Tooltip>
          ) : (
            <div>-</div>
          )}
        </td>
        <td
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            flex: 1,
          }}
        >
          <div style={{flex: 1}}>
            <div>{`Mode: ${mode}`}</div>
          </div>
        </td>
      </tr>
    );
  }

  const {status, runningScheduleCount, ticks, runs, runsCount, scheduleOriginId} = scheduleState;

  const latestTick = ticks.length > 0 ? ticks[0] : null;

  return (
    <tr key={name}>
      <td style={{maxWidth: '64px'}}>
        <Switch
          checked={status === ScheduleStatus.RUNNING}
          large={true}
          disabled={toggleOffInFlight || toggleOnInFlight}
          innerLabelChecked="on"
          innerLabel="off"
          onChange={() => {
            if (status === ScheduleStatus.RUNNING) {
              stopSchedule({
                variables: {scheduleOriginId},
              });
            } else {
              startSchedule({
                variables: {scheduleSelector},
              });
            }
          }}
        />

        {errorDisplay(status, runningScheduleCount)}
      </td>
      <td>{displayName}</td>
      <td>
        <Link to={`/pipeline/${pipelineName}/`}>{pipelineName}</Link>
      </td>
      <td
        style={{
          maxWidth: 150,
        }}
      >
        {cronSchedule ? (
          <Tooltip position={'bottom'} content={cronSchedule}>
            {humanCronString(cronSchedule)}
          </Tooltip>
        ) : (
          <div>-</div>
        )}
      </td>
      <td style={{maxWidth: 100}}>
        {latestTick ? (
          <TickTag status={latestTick.status} eventSpecificData={latestTick.tickSpecificData} />
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
        )}
      </td>
      <td>
        <div style={{display: 'flex'}}>
          {runs.map((run) => {
            const [partition] = run.tags
              .filter((tag) => tag.key === 'dagster/partition')
              .map((tag) => tag.value);
            const runLabel = partition ? (
              <>
                <div>Run id: {titleForRun(run)}</div>
                <div>Partition: {partition}</div>
              </>
            ) : (
              titleForRun(run)
            );
            return (
              <div
                style={{
                  cursor: 'pointer',
                  marginRight: '4px',
                }}
                key={run.runId}
              >
                <Link to={`/instance/runs/${run.runId}`}>
                  <Tooltip
                    position={'top'}
                    content={runLabel}
                    wrapperTagName="div"
                    targetTagName="div"
                  >
                    <RunStatus status={run.status} />
                  </Tooltip>
                </Link>
              </div>
            );
          })}
        </div>
        {runsCount > NUM_RUNS_TO_DISPLAY && (
          <Link
            to={`/instance/runs/?q=${encodeURIComponent(`tag:dagster/schedule_name=${name}`)}`}
            style={{verticalAlign: 'top'}}
          >
            {' '}
            +{runsCount - NUM_RUNS_TO_DISPLAY} more
          </Link>
        )}
      </td>
      <td>
        <div style={{display: 'flex', alignItems: 'center'}}>
          <div>{`Mode: ${mode}`}</div>
          <Popover
            content={
              yamlLoading ? (
                <div style={{padding: '16px'}}>
                  <Spinner size={16} />
                </div>
              ) : (
                <Menu>
                  <MenuItem
                    text="View Configuration..."
                    icon="share"
                    onClick={() => {
                      if (runConfigError) {
                        showCustomAlert({
                          body: <PythonErrorInfo error={runConfigError} />,
                        });
                      } else {
                        showCustomAlert({
                          title: 'Config',
                          body: (
                            <HighlightedCodeBlock
                              value={runConfigYaml || 'Unable to resolve config'}
                              languages={['yaml']}
                            />
                          ),
                        });
                      }
                    }}
                  />
                  <MenuItem
                    text="Open in Playground..."
                    icon="edit"
                    target="_blank"
                    disabled={!runConfigYaml}
                    href={`/pipeline/${pipelineName}/playground/setup?${qs.stringify({
                      mode,
                      solidSelection,
                      config: runConfigYaml,
                    })}`}
                  />

                  {schedule.partitionSet?.name ? (
                    <MenuItem
                      text="View Partition History..."
                      icon="multi-select"
                      target="_blank"
                      href={`/pipeline/${pipelineName}/partitions`}
                    />
                  ) : null}
                </Menu>
              )
            }
            position={'bottom'}
          >
            <Button
              small
              minimal
              icon="chevron-down"
              onClick={() => {
                setConfigRequested(true);
              }}
              style={{marginLeft: '4px'}}
            />
          </Popover>
        </div>
      </td>
    </tr>
  );
};

export const ScheduleRowHeader: React.FunctionComponent<{
  schedule: ScheduleDefinitionFragment;
}> = ({schedule}) => {
  if (!schedule.scheduleState) {
    return (
      <tr>
        <th>Schedule Name</th>
        <th>Pipeline</th>
        <th>Schedule</th>
        <th>Execution Params</th>
      </tr>
    );
  } else {
    return (
      <tr>
        <th></th>
        <th>Schedule Name</th>
        <th>Pipeline</th>
        <th>Schedule</th>
        <th>Last Tick</th>
        <th>Latest Runs</th>
        <th>Execution Params</th>
      </tr>
    );
  }
};

export const ScheduleStateRow: React.FunctionComponent<{
  scheduleState: ScheduleStateFragment;
  showStatus?: boolean;
  dagsterRepoOption?: DagsterRepoOption;
}> = ({scheduleState, showStatus = false, dagsterRepoOption}) => {
  const [startSchedule, {loading: toggleOnInFlight}] = useMutation(START_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });

  const history = useHistory();
  const confirm = useConfirmation();
  const {options} = useRepositoryOptions();
  const [, setRepo] = useCurrentRepositoryState(options);
  const [showRepositoryOrigin, setShowRepositoryOrigin] = useState(false);

  const {
    status,
    scheduleName,
    cronSchedule,
    ticks,
    runs,
    runsCount,
    scheduleOriginId,
    repositoryOrigin,
  } = scheduleState;
  const latestTick = ticks.length > 0 ? ticks[0] : null;

  const goToSchedule = () => {
    if (!dagsterRepoOption) {
      return;
    }
    setRepo(dagsterRepoOption);
    history.push(`/schedules/${scheduleName}`);
  };

  const switchScheduleStatus = async (
    status: ScheduleStatus,
    confirm: (options: ConfirmationOptions) => Promise<void>,
    dagsterRepoOption?: DagsterRepoOption,
  ) => {
    if (!dagsterRepoOption) {
      if (status === ScheduleStatus.RUNNING) {
        // If we don't have the dagster repo in context, then we can only switch the schedule off.
        // Before doing so, we alert the user that we can't switch the schedule back on
        await confirm({
          title: 'Are you sure you want to stop this schedule?',
          description:
            'The schedule definition for this schedule is not available.' +
            'If you turn off this schedule, you will not be able to turn it back on from ' +
            'this currently loaded workspace.',
        });
        stopSchedule({
          variables: {scheduleOriginId},
        });
      }
      return;
    }

    if (status === ScheduleStatus.RUNNING) {
      stopSchedule({
        variables: {scheduleOriginId},
      });
    } else {
      const scheduleSelector = scheduleSelectorWithRepository(
        scheduleName,
        repositorySelectorFromDagsterRepoOption(dagsterRepoOption),
      );

      startSchedule({
        variables: {scheduleSelector},
      });
    }
  };

  return (
    <tr key={scheduleName}>
      {showStatus && (
        <td style={{maxWidth: 60, paddingLeft: 0, textAlign: 'center'}}>
          <Switch
            checked={status === ScheduleStatus.RUNNING}
            large={true}
            disabled={
              (!dagsterRepoOption && status !== ScheduleStatus.RUNNING) ||
              toggleOffInFlight ||
              toggleOnInFlight
            }
            innerLabelChecked="on"
            innerLabel="off"
            onChange={() => switchScheduleStatus(status, confirm, dagsterRepoOption)}
          />
        </td>
      )}

      {dagsterRepoOption ? (
        <td>
          <ButtonLink onClick={goToSchedule}>{scheduleName}</ButtonLink>
        </td>
      ) : (
        <td>
          <div style={{display: 'flex', alignItems: 'base'}}>
            <div>{scheduleName}</div>
            <ButtonLink onClick={() => setShowRepositoryOrigin(!showRepositoryOrigin)}>
              show info{' '}
              <Icon
                icon={showRepositoryOrigin ? IconNames.CHEVRON_DOWN : IconNames.CHEVRON_RIGHT}
              />
            </ButtonLink>
          </div>
          {showRepositoryOrigin && (
            <Callout style={{marginTop: 10}}>
              <RepositoryOriginInformation origin={repositoryOrigin} />
            </Callout>
          )}
        </td>
      )}
      <td
        style={{
          maxWidth: 150,
        }}
      >
        <div
          style={{
            position: 'relative',
            width: '100%',
            whiteSpace: 'pre-wrap',
            display: 'block',
          }}
        >
          {cronSchedule ? (
            <Tooltip position={'bottom'} content={cronSchedule}>
              {humanCronString(cronSchedule)}
            </Tooltip>
          ) : (
            <div>-</div>
          )}
        </div>
      </td>
      <td>
        {latestTick ? (
          <TickTag status={latestTick.status} eventSpecificData={latestTick.tickSpecificData} />
        ) : null}
      </td>
      <td>
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <div style={{display: 'flex'}}>
            {runs.map((run) => {
              return (
                <div
                  style={{
                    cursor: 'pointer',
                    marginRight: '4px',
                  }}
                  key={run.runId}
                >
                  <Link to={`/instance/runs/${run.runId}`}>
                    <Tooltip
                      position={'top'}
                      content={titleForRun(run)}
                      wrapperTagName="div"
                      targetTagName="div"
                    >
                      <RunStatus status={run.status} />
                    </Tooltip>
                  </Link>
                </div>
              );
            })}
          </div>
          {runsCount > NUM_RUNS_TO_DISPLAY && (
            <Link
              to={`/instance/runs/?q=${encodeURIComponent(
                `tag:dagster/schedule_name=${scheduleName}`,
              )}`}
              style={{verticalAlign: 'top'}}
            >
              {' '}
              +{runsCount - NUM_RUNS_TO_DISPLAY} more
            </Link>
          )}
        </div>
      </td>
    </tr>
  );
};

export const TickTag: React.FunctionComponent<{
  status: ScheduleTickStatus;
  eventSpecificData: TickSpecificData;
}> = ({status, eventSpecificData}) => {
  switch (status) {
    case ScheduleTickStatus.STARTED:
      return (
        <Tag minimal={true} intent={Intent.PRIMARY}>
          Started
        </Tag>
      );
    case ScheduleTickStatus.SUCCESS:
      if (!eventSpecificData || eventSpecificData.__typename !== 'ScheduleTickSuccessData') {
        return (
          <Tag minimal={true} intent={Intent.SUCCESS}>
            Success
          </Tag>
        );
      } else {
        return (
          <a
            href={`/instance/runs/${eventSpecificData.run?.runId}`}
            style={{textDecoration: 'none'}}
          >
            <Tag minimal={true} intent={Intent.SUCCESS} interactive={true}>
              Success
            </Tag>
          </a>
        );
      }
    case ScheduleTickStatus.SKIPPED:
      return (
        <Tag minimal={true} intent={Intent.WARNING}>
          Skipped
        </Tag>
      );
    case ScheduleTickStatus.FAILURE:
      if (!eventSpecificData || eventSpecificData.__typename !== 'ScheduleTickFailureData') {
        return (
          <Tag minimal={true} intent={Intent.DANGER}>
            Failure
          </Tag>
        );
      } else {
        return (
          <LinkButton
            onClick={() =>
              showCustomAlert({
                title: 'Schedule Response',
                body: <PythonErrorInfo error={eventSpecificData.error} />,
              })
            }
          >
            <Tag minimal={true} intent={Intent.DANGER} interactive={true}>
              Failure
            </Tag>
          </LinkButton>
        );
      }
    default:
      return assertUnreachable(status);
  }
};

const FETCH_SCHEDULE_YAML = gql`
  query FetchScheduleYaml($scheduleSelector: ScheduleSelector!) {
    scheduleDefinitionOrError(scheduleSelector: $scheduleSelector) {
      ... on ScheduleDefinition {
        runConfigOrError {
          ... on ScheduleRunConfig {
            yaml
          }
          ... on PythonError {
            ...PythonErrorFragment
          }
        }
      }
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
`;

const START_SCHEDULE_MUTATION = gql`
  mutation StartSchedule($scheduleSelector: ScheduleSelector!) {
    startSchedule(scheduleSelector: $scheduleSelector) {
      __typename
      ... on ScheduleStateResult {
        scheduleState {
          __typename
          id
          runningScheduleCount
          status
        }
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

const STOP_SCHEDULE_MUTATION = gql`
  mutation StopSchedule($scheduleOriginId: String!) {
    stopRunningSchedule(scheduleOriginId: $scheduleOriginId) {
      __typename
      ... on ScheduleStateResult {
        scheduleState {
          __typename
          id
          runningScheduleCount
          status
        }
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

const LinkButton = styled.button`
  background: inherit;
  border: none;
  cursor: pointer;
  font-size: inherit;
  text-decoration: none;
  padding: 0;
`;
