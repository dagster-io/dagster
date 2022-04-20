import {gql, useQuery} from '@apollo/client';
import {Box, Colors, Spinner, Tooltip} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';

import {AssetValueGraph, AssetValueGraphData} from '../assets/AssetValueGraph';
import {StepStatusDot} from '../gantt/GanttStatusPanel';
import {linkToRunEvent} from '../runs/RunUtils';
import {RepoAddress} from '../workspace/types';

import {SidebarSection} from './SidebarComponents';
import {SidebarOpGraphsQuery, SidebarOpGraphsQueryVariables} from './types/SidebarOpGraphsQuery';

export const StateColors = {
  SUCCESS: Colors.Green500,
  FAILURE: Colors.Red500,
  SKIPPED: Colors.Gray500,
};

export const SidebarOpExecutionGraphs: React.FC<{
  handleID: string;
  solidName: string;
  pipelineName: string;
  repoAddress: RepoAddress;
}> = ({repoAddress, handleID, pipelineName, solidName}) => {
  const [highlightedStartTime, setHighlightedStartTime] = React.useState<number | null>(null);
  const result = useQuery<SidebarOpGraphsQuery, SidebarOpGraphsQueryVariables>(
    SIDEBAR_OP_GRAPHS_QUERY,
    {
      variables: {
        handleID,
        selector: {
          repositoryName: repoAddress.name,
          repositoryLocationName: repoAddress.location,
          pipelineName,
        },
      },
      fetchPolicy: 'cache-and-network',
    },
  );
  const stepStats =
    result.data?.pipelineOrError.__typename === 'Pipeline'
      ? result.data.pipelineOrError.solidHandle?.stepStats
      : undefined;

  const nodes =
    stepStats && stepStats.__typename === 'SolidStepStatsConnection' ? stepStats.nodes : null;

  const executionTime = React.useMemo(() => {
    const values = nodes
      ? nodes
          .filter((s) => s.startTime && s.endTime)
          .map((s) => ({
            x: Number(s.startTime) * 1000,
            xNumeric: Number(s.startTime) * 1000,
            y: s.endTime! - s.startTime!,
          }))
      : [];

    const xs = values.map((v) => v.xNumeric);
    const ys = values.map((v) => v.y).filter((v) => !isNaN(v));
    const data: AssetValueGraphData = {
      xAxis: 'time',
      values,
      minXNumeric: Math.min(...xs),
      maxXNumeric: Math.max(...xs),
      minY: Math.min(...ys),
      maxY: Math.max(...ys),
    };
    return data;
  }, [nodes]);

  if (stepStats?.__typename === 'SolidStepStatusUnavailableError') {
    return <span />;
  }

  const displayed = (nodes || []).slice(0, 10);

  return (
    <>
      <SidebarSection title="Execution Time">
        <Box flex={{alignItems: 'center', justifyContent: 'center'}}>
          {result.loading ? (
            <Spinner purpose="section" />
          ) : (
            <AssetValueGraph
              label="Step Execution Time"
              yAxisLabel="Seconds"
              width="100%"
              data={executionTime}
              xHover={highlightedStartTime}
              onHoverX={(v) => setHighlightedStartTime(v ? Number(v) : null)}
            />
          )}
        </Box>
      </SidebarSection>
      <SidebarSection title="Execution Status">
        <Box padding={{left: 24, right: 16, vertical: 12}}>
          <Box flex={{gap: 16}} style={{fontSize: '0.8rem'}}>
            <div style={{flex: 1}}>{`Last ${displayed.length} Run${
              displayed.length !== 1 ? 's' : ''
            }`}</div>
            <Box style={{overflowX: 'auto'}} flex={{gap: 2}}>
              {displayed.reverse().map(({runId, status, startTime}) => (
                <Tooltip
                  key={runId}
                  placement="bottom-end"
                  content={`View Run ${runId.slice(0, 8)} →`}
                >
                  <Link to={linkToRunEvent({runId}, {stepKey: solidName})}>
                    <StepStatusDot
                      onMouseEnter={() => startTime && setHighlightedStartTime(startTime * 1000)}
                      onMouseLeave={() => setHighlightedStartTime(null)}
                      style={{
                        border: `2px solid ${
                          startTime && startTime * 1000 === highlightedStartTime
                            ? Colors.Blue500
                            : 'transparent'
                        }`,
                        backgroundColor: status ? StateColors[status] : Colors.Gray200,
                      }}
                    />
                  </Link>
                </Tooltip>
              ))}
            </Box>
          </Box>
        </Box>
      </SidebarSection>
    </>
  );
};

const SIDEBAR_OP_GRAPHS_QUERY = gql`
  query SidebarOpGraphsQuery($selector: PipelineSelector!, $handleID: String!) {
    pipelineOrError(params: $selector) {
      __typename
      ... on Pipeline {
        id
        name
        solidHandle(handleID: $handleID) {
          stepStats(limit: 20) {
            __typename

            ... on SolidStepStatsConnection {
              nodes {
                runId
                startTime
                endTime
                status
              }
            }
            ... on SolidStepStatusUnavailableError {
              __typename
            }
          }
        }
      }
    }
  }
`;
