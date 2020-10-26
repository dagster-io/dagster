import {gql, useQuery} from '@apollo/client';
import {Spinner} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {RunStatsQuery, RunStatsQueryVariables} from 'src/runs/types/RunStatsQuery';

export const RunStats = ({runId}: {runId: string}) => {
  const stats = useQuery<RunStatsQuery, RunStatsQueryVariables>(RUN_STATS_QUERY, {
    variables: {runId},
  });

  if (stats.loading || !stats.data) {
    return (
      <RunStatsDetailsContainer>
        <div style={{padding: 25, textAlign: 'center'}}>
          <Spinner size={22} />
        </div>
      </RunStatsDetailsContainer>
    );
  }

  const result = stats.data.pipelineRunOrError;

  if (result.__typename !== 'PipelineRun') {
    return <PythonErrorInfo error={result} />;
  }
  if (result.stats.__typename !== 'PipelineRunStatsSnapshot') {
    return <PythonErrorInfo error={result.stats} />;
  }

  const runPath = `/pipeline/${result.pipelineName}/runs/${runId}`;
  return (
    <RunStatsDetailsContainer>
      <Link
        to={`${runPath}?q=type:step_success`}
      >{`${result.stats.stepsSucceeded} steps succeeded`}</Link>
      <Link to={`${runPath}?q=type:step_failure`}>
        {`${result.stats.stepsFailed} steps failed`}
      </Link>
      <Link
        to={`${runPath}/${runId}?q=type:materialization`}
      >{`${result.stats.materializations} materializations`}</Link>
      <Link
        to={`${runPath}?q=type:expectation`}
      >{`${result.stats.expectations} expectations passed`}</Link>
    </RunStatsDetailsContainer>
  );
};

export const RUN_STATS_QUERY = gql`
  query RunStatsQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      __typename
      ... on PythonError {
        ...PythonErrorFragment
      }
      ... on PipelineRunNotFoundError {
        message
      }
      ... on PipelineRun {
        runId
        pipelineName
        stats {
          ... on PipelineRunStatsSnapshot {
            stepsSucceeded
            stepsFailed
            expectations
            materializations
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

export const RunStatsDetailsContainer = styled.div`
  min-width: 200px;
  padding: 20px;
  color: white;
  & > a {
    display: block;
  }
`;
