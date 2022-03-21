import {gql, useQuery} from '@apollo/client';
import {
  Box,
  ButtonWIP,
  ButtonLink,
  ColorsWIP,
  DialogBody,
  DialogFooter,
  DialogWIP,
  Group,
  IconWIP,
  NonIdealState,
  Spinner,
  TagWIP,
  Body,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {assertUnreachable} from '../app/Util';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {InstigationTickStatus, InstigationType} from '../types/globalTypes';

import {LaunchedRunListQuery, LaunchedRunListQueryVariables} from './types/LaunchedRunListQuery';
import {TickTagFragment} from './types/TickTagFragment';

export const TickTag: React.FC<{
  tick: TickTagFragment;
  instigationType?: InstigationType;
}> = ({tick, instigationType}) => {
  const [open, setOpen] = React.useState<boolean>(false);
  switch (tick.status) {
    case InstigationTickStatus.STARTED:
      return <TagWIP>Started</TagWIP>;
    case InstigationTickStatus.SUCCESS:
      if (!tick.runIds.length) {
        return <TagWIP intent="primary">Requested</TagWIP>;
      }
      const tag = (
        <>
          <TagWIP intent="primary" interactive>
            <ButtonLink underline="never" onClick={() => setOpen(true)}>
              {tick.runIds.length} Requested
            </ButtonLink>
          </TagWIP>
          <DialogWIP
            isOpen={open}
            onClose={() => setOpen(false)}
            style={{width: '90vw'}}
            title="Launched runs"
          >
            <DialogBody>{open && <RunList runIds={tick.runIds} />}</DialogBody>
            <DialogFooter>
              <ButtonWIP intent="primary" onClick={() => setOpen(false)}>
                OK
              </ButtonWIP>
            </DialogFooter>
          </DialogWIP>
        </>
      );
      if (tick.runKeys.length > tick.runIds.length) {
        const message = `${tick.runKeys.length} runs requested, but ${
          tick.runKeys.length - tick.runIds.length
        } skipped because the runs already exist for those requested keys.`;
        return (
          <Tooltip position="right" content={message}>
            {tag}
          </Tooltip>
        );
      }
      return tag;

    case InstigationTickStatus.SKIPPED:
      if (tick.runKeys) {
        const message = `${tick.runKeys.length} runs requested, but skipped because the runs already exist for the requested keys.`;
        return (
          <Tooltip position="right" content={message}>
            <TagWIP intent="warning">Skipped</TagWIP>
          </Tooltip>
        );
      }
      if (tick.skipReason) {
        return (
          <Tooltip position="right" content={tick.skipReason} targetTagName="div">
            <TagWIP intent="warning">Skipped</TagWIP>
          </Tooltip>
        );
      }
      return <TagWIP intent="warning">Skipped</TagWIP>;
    case InstigationTickStatus.FAILURE:
      if (!tick.error) {
        return <TagWIP intent="danger">Failure</TagWIP>;
      } else {
        const error = tick.error;
        const showError = () =>
          showCustomAlert({
            title: instigationType
              ? instigationType === InstigationType.SCHEDULE
                ? 'Schedule Response'
                : 'Sensor Response'
              : 'Python Error',
            body: <PythonErrorInfo error={error} />,
          });
        return (
          <>
            <LinkButton onClick={showError}>
              <TagWIP minimal={true} intent="danger">
                Failure
              </TagWIP>
            </LinkButton>
            <ButtonLink onClick={showError} style={{marginLeft: 8, fontSize: 14}}>
              View error
            </ButtonLink>
          </>
        );
      }
    default:
      return assertUnreachable(tick.status);
  }
};

export const RunList: React.FC<{
  runIds: string[];
}> = ({runIds}) => {
  const {data, loading} = useQuery<LaunchedRunListQuery, LaunchedRunListQueryVariables>(
    LAUNCHED_RUN_LIST_QUERY,
    {
      variables: {
        filter: {
          runIds,
        },
      },
    },
  );

  if (loading || !data) {
    return <Spinner purpose="section" />;
  }

  if (data.pipelineRunsOrError.__typename !== 'Runs') {
    return (
      <NonIdealState
        icon="error"
        title="Query Error"
        description={data.pipelineRunsOrError.message}
      />
    );
  }
  return (
    <div>
      <RunTable runs={data.pipelineRunsOrError.results} onSetFilter={() => {}} />
    </div>
  );
};

export const FailedRunList: React.FC<{
  originRunIds?: string[];
}> = ({originRunIds}) => {
  if (!originRunIds || !originRunIds.length) {
    return null;
  }
  return (
    <Group direction="column" spacing={16}>
      <Box padding={12} border={{side: 'bottom', width: 1, color: ColorsWIP.Gray200}}>
        <Body>
          Failed Runs
          <Tooltip content="Failed runs this tick reacted on and reported back to.">
            <IconWIP name="info" color={ColorsWIP.Gray500} />
          </Tooltip>
        </Body>

        <RunList runIds={originRunIds} />
      </Box>
      <Box padding={12} margin={{bottom: 8}}>
        <Body>
          Requested Runs
          <Tooltip content="Runs launched by the run requests in this tick.">
            <IconWIP name="info" color={ColorsWIP.Gray500} />
          </Tooltip>
        </Body>
        <NonIdealState
          icon="sensors"
          title="No runs to display"
          description="This sensor does not target a pipeline or job."
        />
      </Box>
    </Group>
  );
};
const LinkButton = styled.button`
  background: inherit;
  border: none;
  cursor: pointer;
  font-size: inherit;
  text-decoration: none;
  padding: 0;
`;

export const TICK_TAG_FRAGMENT = gql`
  fragment TickTagFragment on InstigationTick {
    id
    status
    timestamp
    skipReason
    runIds
    runKeys
    error {
      ...PythonErrorFragment
    }
  }
`;

const LAUNCHED_RUN_LIST_QUERY = gql`
  query LaunchedRunListQuery($filter: RunsFilter!) {
    pipelineRunsOrError(filter: $filter, limit: 500) {
      ... on PipelineRuns {
        results {
          ...RunTableRunFragment
          id
          runId
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ...PythonErrorFragment
    }
  }
  ${RUN_TABLE_RUN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
