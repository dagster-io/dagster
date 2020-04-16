import * as React from "react";

import { Query, QueryResult } from "react-apollo";
import {
  PartitionLongitudinalQuery,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_executionPlan
} from "./types/PartitionLongitudinalQuery";
import { Header, RowContainer } from "../ListComponents";
import gql from "graphql-tag";
import { Link } from "react-router-dom";
import { GraphQueryInput } from "../GraphQueryInput";
import { filterByQuery, GraphQueryItem } from "../GraphQueryImpl";
import { GaantChart, toGraphQueryItems } from "../gaant/GaantChart";

import { RunStatus } from "../runs/RunUtils";
import styled from "styled-components/macro";
import { Divider, Button, ButtonGroup, Spinner } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { Line } from "react-chartjs-2";
import { colorHash } from "../Util";
import Loading from "../Loading";

type Partition = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results;
type ExecutionPlan = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_executionPlan;
type Run = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs;

interface PartitionViewProps {
  partitionSetName: string;
  cursor: string | undefined;
  setCursor: (cursor: string | undefined) => void;
}

export const PartitionView: React.FunctionComponent<PartitionViewProps> = ({
  partitionSetName,
  cursor,
  setCursor
}) => {
  const [cursorStack, setCursorStack] = React.useState<string[]>([]);
  const [pageSize, setPageSize] = React.useState<number>(7);
  const popCursor = () => {
    const nextStack = [...cursorStack];
    setCursor(nextStack.pop());
    setCursorStack(nextStack);
  };
  const pushCursor = (nextCursor: string) => {
    if (cursor) setCursorStack([...cursorStack, cursor]);
    setCursor(nextCursor);
  };

  return (
    <Query
      query={PARTITION_SET_QUERY}
      variables={{
        partitionSetName,
        partitionsCursor: cursor,
        partitionsLimit: pageSize + 1
      }}
      fetchPolicy="cache-and-network"
      partialRefetch={true}
    >
      {(queryResult: QueryResult<PartitionLongitudinalQuery, any>) => (
        <Loading queryResult={queryResult} allowStaleData={true}>
          {({ partitionSetOrError }) => {
            if (partitionSetOrError.__typename !== "PartitionSet") {
              return null;
            }
            const partitionSet = partitionSetOrError;
            const partitions = partitionSet.partitions.results;
            const latestRun = getLatestRun(partitions);
            const executionPlan: ExecutionPlan | null | undefined =
              latestRun?.executionPlan;

            return (
              <div style={{ marginTop: 30 }}>
                <Header>{`Partition Set: ${partitionSetName}`}</Header>
                <Divider />
                <PartitionPagerControls
                  displayed={partitions.slice(0, pageSize)}
                  setPageSize={setPageSize}
                  hasNextPage={partitions.length === pageSize + 1}
                  hasPrevPage={!!cursor}
                  pushCursor={pushCursor}
                  popCursor={popCursor}
                  setCursor={setCursor}
                />
                <div style={{ position: "relative" }}>
                  <PartitionTable partitions={partitions} />
                  <PartitionGraph
                    partitions={partitions}
                    executionPlan={executionPlan}
                    generateData={_getDurationData}
                  />
                  <PartitionGraph
                    partitions={partitions}
                    executionPlan={executionPlan}
                    generateData={_getMaterializationData}
                  />
                  <PartitionGraph
                    partitions={partitions}
                    executionPlan={executionPlan}
                    generateData={_getExpectationsSuccess}
                  />
                  <PartitionGraph
                    partitions={partitions}
                    executionPlan={executionPlan}
                    generateData={_getExpectationsFailure}
                  />
                  <PartitionGraph
                    partitions={partitions}
                    executionPlan={executionPlan}
                    generateData={_getExpectationsRate}
                  />
                  {queryResult.loading ? (
                    <Overlay>
                      <Spinner size={48} />
                    </Overlay>
                  ) : null}
                </div>
              </div>
            );
          }}
        </Loading>
      )}
    </Query>
  );
};

const Overlay = styled.div`
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-color: #ffffff;
  opacity: 0.8;
  z-index: 3;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const getLatestRun = (partitions: Partition[]) => {
  let runs: Run[] = [];
  partitions.forEach(partition => {
    runs = runs.concat(partition.runs);
  });
  runs.sort((a: Run, b: Run) => {
    if (
      a.stats.__typename !== "PipelineRunStatsSnapshot" &&
      b.stats.__typename !== "PipelineRunStatsSnapshot"
    ) {
      return 0;
    }
    if (a.stats.__typename !== "PipelineRunStatsSnapshot") {
      return -1;
    }
    if (b.stats.__typename !== "PipelineRunStatsSnapshot") {
      return 1;
    }

    return (b.stats.endTime || 0) - (a.stats.endTime || 0);
  });

  if (!runs.length) {
    return undefined;
  }
  return runs[0];
};

interface PartitionGraphProps {
  partitions: Partition[];
  executionPlan: ExecutionPlan | null | undefined;
  generateData: (partitions: Partition[]) => { [key: string]: any };
}

const _getDurationData = (partitions: Partition[]) => {
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {};
  partitions.forEach(partition => {
    const runs = partition.runs;
    if (!runs || !runs.length) {
      return;
    }
    const { stats, stepStats } = runs[runs.length - 1];
    const key = "Pipeline Execution Time";
    if (
      stats &&
      stats.__typename === "PipelineRunStatsSnapshot" &&
      stats.endTime &&
      stats.startTime
    ) {
      points[key] = [
        ...(points[key] || []),
        { x: partition.name, y: stats.endTime - stats.startTime }
      ];
    }
    stepStats.forEach(stepStat => {
      if (stepStat.endTime && stepStat.startTime) {
        points[stepStat.stepKey] = [
          ...(points[stepStat.stepKey] || []),
          { x: partition.name, y: stepStat.endTime - stepStat.startTime }
        ];
      }
    });
  });

  return points;
};

const _getMaterializationData = (partitions: Partition[]) => {
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {};
  partitions.forEach(partition => {
    const runs = partition.runs;
    if (!runs || !runs.length) {
      return;
    }
    const { stats, stepStats } = runs[runs.length - 1];
    const key = "Total Materializations";
    if (stats && stats.__typename === "PipelineRunStatsSnapshot") {
      points[key] = [
        ...(points[key] || []),
        { x: partition.name, y: stats.materializations }
      ];
    }
    stepStats.forEach(stepStat => {
      points[stepStat.stepKey] = [
        ...(points[stepStat.stepKey] || []),
        { x: partition.name, y: stepStat.materializations?.length || 0 }
      ];
    });
  });

  return points;
};

const _getExpectationsSuccess = (partitions: Partition[]) => {
  const pipelineKey = "Total Successes";
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {
    [pipelineKey]: []
  };
  partitions.forEach(partition => {
    const runs = partition.runs;
    if (!runs || !runs.length) {
      return;
    }
    const { stepStats } = runs[runs.length - 1];

    let pipelineSuccessCount = 0;
    stepStats.forEach(stepStat => {
      const successCount =
        stepStat.expectationResults?.filter(x => x.success).length || 0;
      points[stepStat.stepKey] = [
        ...(points[stepStat.stepKey] || []),
        {
          x: partition.name,
          y: successCount
        }
      ];
      pipelineSuccessCount += successCount;
    });
    points[pipelineKey] = [
      ...points[pipelineKey],
      { x: partition.name, y: pipelineSuccessCount }
    ];
  });

  return points;
};

const _getExpectationsFailure = (partitions: Partition[]) => {
  const pipelineKey = "Total Failures";
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {
    [pipelineKey]: []
  };

  partitions.forEach(partition => {
    const runs = partition.runs;
    if (!runs || !runs.length) {
      return;
    }
    const { stepStats } = runs[runs.length - 1];
    let pipelineFailureCount = 0;
    stepStats.forEach(stepStat => {
      const failureCount =
        stepStat.expectationResults?.filter(x => !x.success).length || 0;
      points[stepStat.stepKey] = [
        ...(points[stepStat.stepKey] || []),
        {
          x: partition.name,
          y: failureCount
        }
      ];
      pipelineFailureCount += failureCount;
    });
    points[pipelineKey] = [
      ...points[pipelineKey],
      { x: partition.name, y: pipelineFailureCount }
    ];
  });

  return points;
};

const _getExpectationsRate = (partitions: Partition[]) => {
  const pipelineKey = "Total Rate";
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {
    [pipelineKey]: []
  };
  partitions.forEach(partition => {
    const runs = partition.runs;
    if (!runs || !runs.length) {
      return;
    }
    const { stepStats } = runs[runs.length - 1];
    let pipelineSuccessCount = 0;
    let pipelineTotalCount = 0;
    stepStats.forEach(stepStat => {
      const successCount =
        stepStat.expectationResults?.filter(x => x.success).length || 0;
      const totalCount = stepStat.expectationResults?.length || 0;
      const rate = totalCount ? successCount / totalCount : 0;
      points[stepStat.stepKey] = [
        ...(points[stepStat.stepKey] || []),
        { x: partition.name, y: rate }
      ];
      pipelineSuccessCount += successCount;
      pipelineTotalCount += totalCount;
    });
    points[pipelineKey] = [
      ...points[pipelineKey],
      {
        x: partition.name,
        y: pipelineTotalCount ? pipelineSuccessCount / pipelineTotalCount : 0
      }
    ];
  });

  return points;
};

const fillPartitions = (
  data: { [key: string]: [{ x: string; y: number | null }] },
  partitions: Partition[]
) => {
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {};

  Object.keys(data).forEach(key => {
    const keyData = {};
    (data[key] || []).forEach(dataPoint => {
      keyData[dataPoint.x] = dataPoint.y;
    });
    points[key] = partitions.map(partition => ({
      x: partition.name,
      y: keyData[partition.name] || 0
    }));
  });

  return points;
};

const PartitionGraph: React.FunctionComponent<PartitionGraphProps> = ({
  partitions,
  executionPlan,
  generateData
}) => {
  const graph: GraphQueryItem[] = executionPlan
    ? toGraphQueryItems(executionPlan)
    : [];
  const [query, setQuery] = React.useState("*");
  const onUpdateQuery = (query: string) => {
    setQuery(query);
  };
  const selectedSteps = filterByQuery(graph, query).all.map(node => node.name);
  const data = fillPartitions(generateData(partitions), partitions);
  const graphData = {
    labels: partitions.map(partition => partition.name),
    datasets: Object.keys(data)
      .filter(
        label =>
          !query.trim() || query.trim() === "*" || selectedSteps.includes(label)
      )
      .map(label => ({
        label,
        data: data[label],
        borderColor: colorHash(label),
        backgroundColor: "rgba(0,0,0,0)"
      }))
  };

  return (
    <>
      <div style={{ paddingBottom: 50, position: "relative" }}>
        <GraphQueryInput
          items={graph}
          value={query}
          placeholder="Type a Step Subset"
          onChange={onUpdateQuery}
        />
      </div>
      <RowContainer style={{ marginBottom: 20 }}>
        <Line data={graphData} height={50} />
      </RowContainer>
    </>
  );
};

const PartitionTable: React.FunctionComponent<{ partitions: Partition[] }> = ({
  partitions
}) => {
  return (
    <Container>
      <Gutter>
        <Column>
          <GutterHeader>&nbsp;</GutterHeader>
          <GutterFiller>
            <div>Runs</div>
          </GutterFiller>
        </Column>
      </Gutter>
      {partitions.map(partition => (
        <Column key={partition.name}>
          <ColumnHeader>{partition.name}</ColumnHeader>
          {partition.runs.map(run => (
            <Link
              to={`/runs/all/${run.runId}`}
              key={run.runId}
              style={{ textAlign: "center", lineHeight: 1 }}
            >
              <RunStatus status={run.status} square={true} />
            </Link>
          ))}
        </Column>
      ))}
    </Container>
  );
};

const Gutter = styled.div`
  width: 45px;
  display: flex;
  flex-direction: column-reverse;
`;
const GutterHeader = styled.div`
  font-size: 12px;
  color: #666666;
  padding: 2px 0;
  border-top: 1px solid transparent;
  text-align: center;
`;
const GutterFiller = styled.div`
  font-size: 12px;
  color: #666666;
  border-right: 1px solid #ececec;
  min-height: 50px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  & div {
    transform: rotate(-90deg);
  }
`;
const Container = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: space-around;
  background-color: #ffffff;
  padding: 30px 30px 10px 0;
  overflow-x: auto;
  margin-bottom: 30px;
`;
const Column = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column-reverse;
  align-items: stretch;
  min-width: 50px;
`;
const ColumnHeader = styled.div`
  font-size: 12px;
  color: #666666;
  padding: 2px 0;
  border-top: 1px solid #ececec;
  margin-top: 2px;
  text-align: center;
`;

interface PartitionPagerProps {
  displayed: Partition[] | undefined;
  setPageSize: React.Dispatch<React.SetStateAction<number>>;
  hasPrevPage: boolean;
  hasNextPage: boolean;
  pushCursor: (nextCursor: string) => void;
  popCursor: () => void;
  setCursor: (cursor: string | undefined) => void;
}

const PartitionPagerControls: React.FunctionComponent<PartitionPagerProps> = ({
  displayed,
  setPageSize,
  hasNextPage,
  hasPrevPage,
  setCursor,
  pushCursor,
  popCursor
}) => {
  return (
    <PartitionPagerContainer>
      <ButtonGroup>
        <Button
          onClick={() => {
            setPageSize(7);
          }}
        >
          Week
        </Button>
        <Button
          onClick={() => {
            if (displayed && displayed.length < 31) {
              setCursor(undefined);
            }
            setPageSize(31);
          }}
        >
          Month
        </Button>
        <Button
          onClick={() => {
            if (displayed && displayed.length < 365) {
              setCursor(undefined);
            }
            setPageSize(365);
          }}
        >
          Year
        </Button>
      </ButtonGroup>

      <ButtonGroup>
        <Button
          disabled={!hasPrevPage}
          icon={IconNames.ARROW_LEFT}
          onClick={() => popCursor()}
        >
          Back
        </Button>
        <Button
          disabled={!hasNextPage}
          rightIcon={IconNames.ARROW_RIGHT}
          onClick={() =>
            displayed && pushCursor(displayed[displayed.length - 1].name)
          }
        >
          Next
        </Button>
      </ButtonGroup>
    </PartitionPagerContainer>
  );
};

const PartitionPagerContainer = styled.div`
  display: flex;
  justify-content: space-between;
  margin: 10px 0;
`;

const PARTITION_SET_QUERY = gql`
  query PartitionLongitudinalQuery(
    $partitionSetName: String!
    $partitionsLimit: Int
    $partitionsCursor: String
  ) {
    partitionSetOrError(partitionSetName: $partitionSetName) {
      ... on PartitionSet {
        name
        partitions(cursor: $partitionsCursor, limit: $partitionsLimit) {
          results {
            name
            runs {
              runId
              tags {
                key
                value
              }
              stats {
                __typename
                ... on PipelineRunStatsSnapshot {
                  startTime
                  endTime
                  materializations
                }
              }
              stepStats {
                __typename
                stepKey
                startTime
                endTime
                materializations {
                  __typename
                }
                expectationResults {
                  success
                }
              }
              status
              executionPlan {
                ...GaantChartExecutionPlanFragment
              }
            }
          }
        }
      }
    }
  }
  ${GaantChart.fragments.GaantChartExecutionPlanFragment}
`;
