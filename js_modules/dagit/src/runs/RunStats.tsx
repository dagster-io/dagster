import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {RunStatsQuery, RunStatsQueryVariables} from 'src/runs/types/RunStatsQuery';
import {Box} from 'src/ui/Box';
import {Spinner} from 'src/ui/Spinner';

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
        to={`${runPath}?logs=type:step_success`}
      >{`${result.stats.stepsSucceeded} steps succeeded`}</Link>
      <Link to={`${runPath}?logs=type:step_failure`}>
        {`${result.stats.stepsFailed} steps failed`}
      </Link>
      <Link
        to={`${runPath}?logs=type:materialization`}
      >{`${result.stats.materializations} materializations`}</Link>
      <Link
        to={`${runPath}?logs=type:expectation`}
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
  padding: 20px;
  color: white;
  & > a {
    display: block;
  }
`;
