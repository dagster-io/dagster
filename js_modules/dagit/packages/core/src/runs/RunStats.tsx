import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {Box} from '../ui/Box';
import {Spinner} from '../ui/Spinner';

import {RunStatsQuery, RunStatsQueryVariables} from './types/RunStatsQuery';

export const RunStats = ({runId}: {runId: string}) => {
  const stats = useQuery<RunStatsQuery, RunStatsQueryVariables>(RUN_STATS_QUERY, {
    variables: {runId},
  });

  if (stats.loading || !stats.data) {
    return (
      <RunStatsDetailsContainer>
        <Box padding={24} flex={{justifyContent: 'center'}}>
          <Spinner purpose="section" />
        </Box>
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

  const runPath = `/instance/runs/${runId}`;
  return (
    <RunStatsDetailsContainer>
      <Link
        to={`${runPath}?logs=type:STEP_SUCCESS`}
      >{`${result.stats.stepsSucceeded} steps succeeded`}</Link>
      <Link to={`${runPath}?logs=type:STEP_FAILURE`}>
        {`${result.stats.stepsFailed} steps failed`}
      </Link>
      <Link
        to={`${runPath}?logs=type:ASSET_MATERIALIZATION`}
      >{`${result.stats.materializations} materializations`}</Link>
      <Link
        to={`${runPath}?logs=type:STEP_EXPECTATION_RESULT`}
      >{`${result.stats.expectations} expectations passed`}</Link>
    </RunStatsDetailsContainer>
  );
};

const RUN_STATS_QUERY = gql`
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
        id
        runId
        pipelineName
        stats {
          ... on PipelineRunStatsSnapshot {
            id
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
  ${PYTHON_ERROR_FRAGMENT}
`;

const RunStatsDetailsContainer = styled.div`
  min-width: 200px;
  padding: 12px;
  color: white;
  font-size: 12px;
  & > a {
    display: block;
  }
`;
