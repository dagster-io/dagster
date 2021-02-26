import {gql, useQuery} from '@apollo/client';
import {
  Tag,
  Tooltip,
  Dialog,
  Button,
  Intent,
  NonIdealState,
  Classes,
  Colors,
} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from 'src/app/CustomAlertProvider';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {assertUnreachable} from 'src/app/Util';
import {
  LaunchedRunListQuery,
  LaunchedRunListQueryVariables,
} from 'src/jobs/types/LaunchedRunListQuery';
import {TickTagFragment} from 'src/jobs/types/TickTagFragment';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from 'src/runs/RunTable';
import {JobTickStatus, JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Spinner} from 'src/ui/Spinner';

export const TickTag: React.FunctionComponent<{
  tick: TickTagFragment;
  jobType?: JobType;
}> = ({tick, jobType}) => {
  const [open, setOpen] = React.useState<boolean>(false);
  switch (tick.status) {
    case JobTickStatus.STARTED:
      return (
        <Tag minimal={true} intent={Intent.NONE}>
          Started
        </Tag>
      );
    case JobTickStatus.SUCCESS:
      if (!tick.runIds.length) {
        return (
          <Tag minimal={true} intent={Intent.PRIMARY}>
            Requested
          </Tag>
        );
      }
      return (
        <>
          <Tag minimal={true} intent={Intent.PRIMARY} interactive={true}>
            <ButtonLink underline="never" onClick={() => setOpen(true)}>
              {tick.runIds.length} Requested
            </ButtonLink>
          </Tag>
          <Dialog
            isOpen={open}
            onClose={() => setOpen(false)}
            style={{width: '90vw'}}
            title={`Launched runs`}
          >
            <Box background={Colors.WHITE} padding={16} margin={{bottom: 16}}>
              {open && <RunList runIds={tick.runIds} />}
            </Box>
            <div className={Classes.DIALOG_FOOTER}>
              <div className={Classes.DIALOG_FOOTER_ACTIONS}>
                <Button intent="primary" onClick={() => setOpen(false)}>
                  OK
                </Button>
              </div>
            </div>
          </Dialog>
        </>
      );
    case JobTickStatus.SKIPPED:
      if (!tick.skipReason) {
        return (
          <Tag minimal={true} intent={Intent.WARNING}>
            Skipped
          </Tag>
        );
      }
      return (
        <Tooltip
          position={'right'}
          content={tick.skipReason}
          wrapperTagName="div"
          targetTagName="div"
        >
          <Tag minimal={true} intent={Intent.WARNING}>
            Skipped
          </Tag>
        </Tooltip>
      );
    case JobTickStatus.FAILURE:
      if (!tick.error) {
        return (
          <Tag minimal={true} intent={Intent.DANGER}>
            Failure
          </Tag>
        );
      } else {
        const error = tick.error;
        return (
          <LinkButton
            onClick={() =>
              showCustomAlert({
                title: jobType
                  ? jobType === JobType.SCHEDULE
                    ? 'Schedule Response'
                    : 'Sensor Response'
                  : 'Python Error',
                body: <PythonErrorInfo error={error} />,
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
      return assertUnreachable(tick.status);
  }
};

export const RunList: React.FunctionComponent<{
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

  if (data.pipelineRunsOrError.__typename !== 'PipelineRuns') {
    return (
      <NonIdealState
        icon={IconNames.ERROR}
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

const LinkButton = styled.button`
  background: inherit;
  border: none;
  cursor: pointer;
  font-size: inherit;
  text-decoration: none;
  padding: 0;
`;

export const TICK_TAG_FRAGMENT = gql`
  fragment TickTagFragment on JobTick {
    id
    status
    timestamp
    skipReason
    runIds
    error {
      ...PythonErrorFragment
    }
  }
`;

const LAUNCHED_RUN_LIST_QUERY = gql`
  query LaunchedRunListQuery($filter: PipelineRunsFilter!) {
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
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }
  ${RUN_TABLE_RUN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
