import {useLazyQuery, useMutation} from '@apollo/client';
import {Button, Colors, Dialog, NonIdealState, Spinner, Switch} from '@blueprintjs/core';
import * as qs from 'query-string';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {HighlightedCodeBlock} from 'src/HighlightedCodeBlock';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {
  displayScheduleMutationErrors,
  FETCH_SCHEDULE_YAML,
  START_SCHEDULE_MUTATION,
  STOP_SCHEDULE_MUTATION,
  TickTag,
} from 'src/schedules/ScheduleRow';
import {humanCronString} from 'src/schedules/humanCronString';
import {FetchScheduleYaml} from 'src/schedules/types/FetchScheduleYaml';
import {ScheduleDefinitionFragment} from 'src/schedules/types/ScheduleDefinitionFragment';
import {ScheduleStatus} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {MetadataTable} from 'src/ui/MetadataTable';
import {Code, Heading} from 'src/ui/Text';
import {FontFamily} from 'src/ui/styles';
import {useScheduleSelector} from 'src/workspace/WorkspaceContext';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

export const ScheduleDetails: React.FC<{
  schedule: ScheduleDefinitionFragment;
  repoAddress: RepoAddress;
}> = (props) => {
  const {repoAddress, schedule} = props;
  const {cronSchedule, name, partitionSet, pipelineName} = schedule;

  const [startSchedule, {loading: toggleOnInFlight}] = useMutation(START_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });

  const scheduleSelector = useScheduleSelector(name);

  const {scheduleState} = schedule;

  // TODO dish: Port over something like the existing UI
  if (!scheduleState) {
    return (
      <NonIdealState
        icon="time"
        title="Schedule not found"
        description={
          <>
            Schedule <strong>{name}</strong> not found in{' '}
            <strong>{repoAddressAsString(repoAddress)}</strong>
          </>
        }
      />
    );
  }

  const {status, ticks, scheduleOriginId} = scheduleState;
  const latestTick = ticks.length > 0 ? ticks[0] : null;

  const onChangeSwitch = () => {
    if (status === ScheduleStatus.RUNNING) {
      stopSchedule({
        variables: {scheduleOriginId},
      });
    } else {
      startSchedule({
        variables: {scheduleSelector},
      });
    }
  };

  return (
    <Group direction="vertical" spacing={12}>
      <Box flex={{alignItems: 'center', justifyContent: 'space-between'}}>
        <Group alignItems="center" direction="horizontal" spacing={8}>
          <Heading>{name}</Heading>
          <Box margin={{left: 4}}>
            <Switch
              checked={status === ScheduleStatus.RUNNING}
              inline
              large
              disabled={toggleOffInFlight || toggleOnInFlight}
              innerLabelChecked="on"
              innerLabel="off"
              onChange={onChangeSwitch}
              style={{margin: '4px 0 0 0'}}
            />
          </Box>
        </Group>
        <ConfigButtons repoAddress={repoAddress} schedule={schedule} />
      </Box>
      <MetadataTable
        rows={[
          {
            key: 'Schedule ID',
            value: <div style={{fontFamily: FontFamily.monospace}}>{scheduleOriginId}</div>,
          },
          {
            key: 'Pipeline',
            value: (
              <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/`)}>
                {pipelineName}
              </Link>
            ),
          },
          {
            key: 'Schedule',
            value: cronSchedule ? (
              <Group direction="horizontal" spacing={8}>
                <span>{humanCronString(cronSchedule)}</span>
                <Code>({cronSchedule})</Code>
              </Group>
            ) : (
              <div>-</div>
            ),
          },
          {
            key: 'Latest tick',
            value: latestTick ? (
              <TickTag status={latestTick.status} eventSpecificData={latestTick.tickSpecificData} />
            ) : (
              <span style={{color: Colors.GRAY4}}>None</span>
            ),
          },
          {
            key: 'Mode',
            value: schedule.mode,
          },
          {
            key: 'Partition set',
            value: partitionSet ? (
              <Link
                to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/partitions`)}
              >
                {partitionSet.name}
              </Link>
            ) : (
              'None'
            ),
          },
        ]}
      />
    </Group>
  );
};

interface ConfigButtonProps {
  repoAddress: RepoAddress;
  schedule: ScheduleDefinitionFragment;
}

const ConfigButtons: React.FC<ConfigButtonProps> = (props) => {
  const {repoAddress, schedule} = props;
  const {mode, name, pipelineName, solidSelection} = schedule;

  const [showDialog, setShowDialog] = React.useState(false);
  const scheduleSelector = useScheduleSelector(name);
  const [fetchYaml, {data, loading}] = useLazyQuery<FetchScheduleYaml>(FETCH_SCHEDULE_YAML, {
    variables: {scheduleSelector},
  });

  const definitionOrError = data?.scheduleDefinitionOrError;
  const {runConfigError, runConfigYaml} = React.useMemo(() => {
    if (!definitionOrError || definitionOrError?.__typename !== 'ScheduleDefinition') {
      return {runConfigError: null, runConfigYaml: null};
    }

    const runConfigError =
      definitionOrError?.runConfigOrError?.__typename === 'PythonError'
        ? definitionOrError.runConfigOrError
        : null;

    const runConfigYaml =
      definitionOrError?.runConfigOrError?.__typename === 'ScheduleRunConfig'
        ? definitionOrError?.runConfigOrError?.yaml
        : null;

    return {runConfigError, runConfigYaml};
  }, [definitionOrError]);

  const dialogBody = () => {
    if (!runConfigError && !runConfigYaml) {
      return `Schedule definition ${name} not found.`;
    }

    if (runConfigError) {
      return (
        <Box
          padding={12}
          background={Colors.WHITE}
          border={{side: 'horizontal', width: 1, color: Colors.LIGHT_GRAY1}}
        >
          <PythonErrorInfo error={runConfigError} />
        </Box>
      );
    }

    if (loading) {
      return (
        <Box padding={64}>
          <Spinner />
        </Box>
      );
    }

    return (
      <Box
        background={Colors.WHITE}
        border={{side: 'horizontal', width: 1, color: Colors.LIGHT_GRAY1}}
        padding={{horizontal: 8, vertical: 4}}
      >
        <HighlightedCodeBlock
          value={runConfigYaml || 'Unable to resolve config'}
          languages={['yaml']}
        />
      </Box>
    );
  };

  const copyYaml = () => {
    if (runConfigYaml) {
      navigator.clipboard.writeText(runConfigYaml);
    }
  };

  const onClickViewConfig = () => {
    fetchYaml();
    setShowDialog(true);
  };

  return (
    <>
      <Group direction="horizontal" spacing={12}>
        <Button icon="share" large={false} onClick={onClickViewConfig}>
          View configuration
        </Button>
        <Button icon="edit" large={false}>
          <PlaygroundLink
            to={workspacePathFromAddress(
              repoAddress,
              `/pipelines/${pipelineName}/playground/setup?${qs.stringify({
                mode,
                solidSelection,
                config: runConfigYaml,
              })}`,
            )}
          >
            Open in Playground
          </PlaygroundLink>
        </Button>
      </Group>
      <Dialog
        icon="info-sign"
        usePortal={true}
        onClose={() => setShowDialog(false)}
        style={{width: '600px', maxWidth: '80vw'}}
        title={`Config: ${name}`}
        isOpen={showDialog}
      >
        <div>{dialogBody()}</div>
        <Box
          background={Colors.LIGHT_GRAY4}
          flex={{justifyContent: 'flex-end'}}
          padding={{top: 16, horizontal: 16}}
        >
          <Group direction="horizontal" spacing={12}>
            {runConfigYaml ? <Button onClick={copyYaml}>Copy</Button> : null}
            <Button intent="primary" autoFocus={true} onClick={() => setShowDialog(false)}>
              OK
            </Button>
          </Group>
        </Box>
      </Dialog>
    </>
  );
};

const PlaygroundLink = styled(Link)`
  &:link,
  &:visited,
  &:hover,
  &:active {
    color: ${Colors.DARK_GRAY1};
    text-decoration: none;
  }
`;
