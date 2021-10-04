import {gql, useQuery} from '@apollo/client';
import {Button} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import qs from 'query-string';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {DagsterTag} from '../runs/RunTag';
import {StepEventStatus} from '../types/globalTypes';
import {ColorsWIP} from '../ui/Colors';
import {NonIdealState} from '../ui/NonIdealState';
import {Spinner} from '../ui/Spinner';

import {STEP_STATUS_COLORS} from './RunMatrixUtils';
import {
  PartitionRunListForStepQuery,
  PartitionRunListForStepQueryVariables,
} from './types/PartitionRunListForStepQuery';

interface StepStats {
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
  materializations: Record<string, unknown>[];
  expectationResults: {success: boolean}[];
}

interface PartitionRunListForStepProps {
  pipelineName: string;
  partitionName: string;
  stepName: string;
  stepStatsByRunId: {
    [runId: string]: StepStats;
  };
}

export const PartitionRunListForStep: React.FunctionComponent<PartitionRunListForStepProps> = (
  props,
) => {
  const {data, loading} = useQuery<
    PartitionRunListForStepQuery,
    PartitionRunListForStepQueryVariables
  >(PARTITION_RUN_LIST_FOR_STEP_QUERY, {
    variables: {
      filter: {
        pipelineName: props.pipelineName,
        tags: [{key: DagsterTag.Partition, value: props.partitionName}],
      },
    },
  });

  if (loading || !data) {
    return <Spinner purpose="section" />;
  }

  if (data.pipelineRunsOrError.__typename !== 'PipelineRuns') {
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
      <RunTable
        runs={data.pipelineRunsOrError.results}
        onSetFilter={() => {}}
        additionalColumnHeaders={[
          <th key="context" style={{maxWidth: 150}}>
            Step Info
          </th>,
        ]}
        additionalColumnsForRow={(run) => [
          <StepStatsColumn
            key="context"
            stats={props.stepStatsByRunId[run.runId] || null}
            linkToLogs={`/instance/runs/${run.runId}?${qs.stringify({
              selection: props.stepName,
              logs: `step:${props.stepName}`,
            })}`}
          />,
        ]}
      />
    </div>
  );
};

const StepStatsColumn: React.FunctionComponent<{
  stats: StepStats | null;
  linkToLogs: string;
}> = ({stats, linkToLogs}) => {
  return (
    <td key="context" style={{maxWidth: 150, borderRight: 0}}>
      {stats ? (
        <div>
          <StatSummaryLine>
            <div
              style={{
                width: 17,
                height: 17,
                background: stats.status ? STEP_STATUS_COLORS[stats.status] : '#eee',
              }}
            />
            <Tooltip content="Expectation Results">
              <StatBox>
                {`${stats.expectationResults.filter((e) => e.success).length} /
      ${stats.expectationResults.length}`}
              </StatBox>
            </Tooltip>
            <Tooltip content="Materializations">
              <StatBox>{`${stats.materializations.length}`}</StatBox>
            </Tooltip>
          </StatSummaryLine>
          <Link to={linkToLogs} component={Button} {...{small: true, rightIcon: 'share'}}>
            Step Logs
          </Link>
        </div>
      ) : (
        <div>No step data.</div>
      )}
    </td>
  );
};

const StatSummaryLine = styled.div`
  display: flex;
  align-items: flex-start;
  margin-bottom: 4px;
`;

const StatBox = styled.div`
  border: 1px solid ${ColorsWIP.Gray100};
  margin-left: 4px;
  padding: 1px 5px;
  font-size: 11px;
`;

const PARTITION_RUN_LIST_FOR_STEP_QUERY = gql`
  query PartitionRunListForStepQuery($filter: PipelineRunsFilter!) {
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
