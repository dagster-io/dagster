import {gql, useMutation, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Menu,
  MenuItem,
  Mono,
  NonIdealState,
  Popover,
  Spinner,
  Subheading,
  Tag,
  useViewport,
} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {TimeContext} from '../app/time/TimeContext';
import {timestampToString} from '../app/time/timestampToString';
import {testId} from '../testing/testId';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {RunRequestTable} from './DryRunRequestTable';
import {RUN_REQUEST_FRAGMENT} from './RunRequestFragment';
import {
  GetScheduleQuery,
  GetScheduleQueryVariables,
  ScheduleDryRunMutation,
  ScheduleDryRunMutationVariables,
} from './types/EvaluateScheduleDialog.types';

const locale = navigator.language;

type Props = {
  repoAddress: RepoAddress;
  name: string;
  onClose: () => void;
  isOpen: boolean;
  jobName: string;
};

export const EvaluateScheduleDialog: React.FC<Props> = (props) => {
  return (
    <Dialog
      {...props}
      style={{width: '70vw', display: 'flex'}}
      title={
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <Icon name="schedule" />
          <span>{props.name}</span>
        </Box>
      }
    >
      <EvaluateSchedule {...props} />
    </Dialog>
  );
};

const EvaluateSchedule: React.FC<Props> = ({repoAddress, name, onClose, jobName}) => {
  const [_selectedTimestamp, setSelectedTimestamp] = React.useState<{ts: number; label: string}>();
  const {data} = useQuery<GetScheduleQuery, GetScheduleQueryVariables>(GET_SCHEDULE_QUERY, {
    variables: {
      scheduleSelector: {
        repositoryLocationName: repoAddress.location,
        repositoryName: repoAddress.name,
        scheduleName: name,
      },
    },
  });
  const {
    timezone: [userTimezone],
  } = React.useContext(TimeContext);
  const [isTickSelectionOpen, setIsTickSelectionOpen] = React.useState<boolean>(false);
  const selectedTimestampRef = React.useRef<{ts: number; label: string} | null>(null);
  const {viewport, containerProps} = useViewport();
  const [shouldEvaluate, setShouldEvaluate] = React.useState(false);
  const content = React.useMemo(() => {
    if (shouldEvaluate) {
      return (
        <EvaluateScheduleContent
          repoAddress={repoAddress}
          name={name}
          timestamp={selectedTimestampRef.current!.ts}
          jobName={jobName}
        />
      );
    }
    if (!data) {
      return (
        <Box padding={{vertical: 48}} flex={{alignItems: 'center', justifyContent: 'center'}}>
          <Spinner purpose="page" />
        </Box>
      );
    }
    if (data.scheduleOrError.__typename === 'PythonError') {
      return <div />;
    }
    if (data.scheduleOrError.__typename === 'ScheduleNotFoundError') {
      return <div />;
    }
    const timestamps = data.scheduleOrError.potentialTickTimestamps.map((ts) => ({
      ts,
      label: timestampToString({
        timestamp: {unix: ts},
        locale,
        timezone: userTimezone,
        timeFormat: {
          showTimezone: true,
        },
      }),
    }));
    selectedTimestampRef.current = _selectedTimestamp || timestamps[0];
    return (
      <SelectWrapper>
        <ScheduleDescriptor>Select a mock evaluation time</ScheduleDescriptor>
        <Popover
          isOpen={isTickSelectionOpen}
          position="bottom-left"
          fill={true}
          content={
            <Menu style={{maxHeight: '400px', overflow: 'scroll', width: `${viewport.width}px`}}>
              {timestamps.map((timestamp) => (
                <MenuItem
                  key={timestamp.ts}
                  text={<div data-testid={testId(`tick-${timestamp.ts}`)}>{timestamp.label}</div>}
                  onClick={() => {
                    setSelectedTimestamp(timestamp);
                    setIsTickSelectionOpen(false);
                  }}
                />
              ))}
            </Menu>
          }
        >
          <div {...containerProps}>
            <Button
              style={{flex: 1}}
              rightIcon={<Icon name="arrow_drop_down" />}
              onClick={() => setIsTickSelectionOpen((isOpen) => !isOpen)}
              data-testid={testId('tick-selection')}
            >
              {selectedTimestampRef.current.label}
            </Button>
          </div>
        </Popover>
      </SelectWrapper>
    );
  }, [
    _selectedTimestamp,
    containerProps,
    data,
    isTickSelectionOpen,
    jobName,
    name,
    repoAddress,
    shouldEvaluate,
    userTimezone,
    viewport.width,
  ]);

  const buttons = React.useMemo(() => {
    if (!shouldEvaluate) {
      return (
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            data-testid={testId('evaluate')}
            intent="primary"
            onClick={() => {
              setShouldEvaluate(true);
            }}
          >
            Evaluate
          </Button>
        </>
      );
    } else {
      return <Button onClick={onClose}>Close</Button>;
    }
  }, [onClose, shouldEvaluate]);

  return (
    <>
      <DialogBody>
        <div style={{minHeight: '300px'}}>{content}</div>
      </DialogBody>
      {buttons ? <DialogFooter topBorder>{buttons}</DialogFooter> : null}
    </>
  );
};

export const GET_SCHEDULE_QUERY = gql`
  query getSchedule(
    $scheduleSelector: ScheduleSelector!
    $startTimestamp: Float
    $ticksAfter: Int
    $ticksBefore: Int
  ) {
    scheduleOrError(scheduleSelector: $scheduleSelector) {
      ... on PythonError {
        message
        stack
      }
      ... on Schedule {
        id
        name
        potentialTickTimestamps(
          startTimestamp: $startTimestamp
          upperLimit: $ticksAfter
          lowerLimit: $ticksBefore
        )
      }
    }
  }
`;

const EvaluateScheduleContent: React.FC<{
  repoAddress: RepoAddress;
  name: string;
  timestamp: number;
  jobName: string;
}> = ({repoAddress, name, timestamp, jobName}) => {
  const {
    timezone: [userTimezone],
  } = React.useContext(TimeContext);
  const [scheduleDryRunMutation] = useMutation<
    ScheduleDryRunMutation,
    ScheduleDryRunMutationVariables
  >(
    SCHEDULE_DRY_RUN_MUTATION,
    React.useMemo(() => {
      const repositorySelector = repoAddressToSelector(repoAddress);
      return {
        variables: {
          selectorData: {
            ...repositorySelector,
            scheduleName: name,
          },
          timestamp,
        },
      };
    }, [name, repoAddress, timestamp]),
  );
  const [result, setResult] = React.useState<Awaited<
    ReturnType<typeof scheduleDryRunMutation>
  > | null>(null);
  React.useEffect(() => {
    scheduleDryRunMutation().then((result) => {
      setResult(() => result);
    });
  }, [scheduleDryRunMutation]);

  if (!result || !result.data) {
    return (
      <Box padding={32} flex={{justifyContent: 'center', alignItems: 'center'}}>
        <Spinner purpose="page" />
      </Box>
    );
  }

  const evaluationResult =
    result?.data?.scheduleDryRun.__typename === 'DryRunInstigationTick'
      ? result?.data?.scheduleDryRun.evaluationResult
      : null;

  const innerContent = () => {
    const data = result.data;
    if (!data || !evaluationResult) {
      return (
        <NonIdealState
          title="An unknown error occurred"
          description={
            <span>
              File an issue on{' '}
              <a href="https://github.com/dagster-io/dagster" target="_blank" rel="noreferrer">
                Github
              </a>{' '}
              if you think this is a bug
            </span>
          }
          icon="error"
        />
      );
    } else if (evaluationResult.error) {
      return <PythonErrorInfo error={evaluationResult.error} />;
    }
    if (!evaluationResult.runRequests?.length) {
      return (
        <div>
          <Subheading>Skip Reason</Subheading>
          <div>{evaluationResult?.skipReason || 'No skip reason was output'}</div>
        </div>
      );
    } else {
      return (
        <RunRequestTable
          runRequests={evaluationResult.runRequests}
          repoAddress={repoAddress}
          isJob={true}
          jobName={jobName}
          name={name}
        />
      );
    }
  };

  const numRunRequests = evaluationResult?.runRequests?.length;
  const error = evaluationResult?.error;

  return (
    <Box flex={{direction: 'column', gap: 8}}>
      <Box>
        <Grid>
          <div>
            <Subheading>Result</Subheading>
            <Box flex={{grow: 1, alignItems: 'center'}}>
              <div>
                {error ? (
                  <Tag intent="danger">Failed</Tag>
                ) : numRunRequests ? (
                  <Tag intent="success">{numRunRequests} run requests</Tag>
                ) : (
                  <Tag intent="warning">Skipped</Tag>
                )}
              </div>
            </Box>
          </div>
          <div>
            <Subheading>Tick</Subheading>
            <Box flex={{grow: 1, alignItems: 'center'}}>
              <Mono>
                {timestampToString({
                  timestamp: {unix: timestamp},
                  locale,
                  timezone: userTimezone,
                  timeFormat: {
                    showTimezone: true,
                  },
                })}
              </Mono>
            </Box>
          </div>
        </Grid>
      </Box>
      {innerContent()}
    </Box>
  );
};
export const SCHEDULE_DRY_RUN_MUTATION = gql`
  mutation ScheduleDryRunMutation($selectorData: ScheduleSelector!, $timestamp: Float) {
    scheduleDryRun(selectorData: $selectorData, timestamp: $timestamp) {
      ...PythonErrorFragment
      ... on DryRunInstigationTick {
        timestamp
        evaluationResult {
          runRequests {
            ...RunRequestFragment
          }
          skipReason
          error {
            ...PythonErrorFragment
          }
        }
      }
      ... on ScheduleNotFoundError {
        scheduleName
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
  ${RUN_REQUEST_FRAGMENT}
`;

const SelectWrapper = styled.div`
  button {
    width: 100%;
    display: flex;
    justify-content: space-between;
  }
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  padding-bottom: 12px;
  border-bottom: 1px solid ${Colors.KeylineGray};
  margin-bottom: 12px;
  ${Subheading} {
    padding-bottom: 4px;
    display: block;
  }
  pre {
    margin: 0;
  }
  button {
    margin-top: 4px;
  }
`;

const ScheduleDescriptor = styled.div`
  padding-bottom: 2px;
`;
