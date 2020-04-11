import * as React from "react";

import { Header, RowColumn, RowContainer } from "../ListComponents";
import { useQuery } from "react-apollo";
import {
  ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet_partitions_results
} from "./types/ScheduleRootQuery";
import {
  PartitionRunsQuery,
  PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results,
  PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan
} from "./types/PartitionRunsQuery";
import gql from "graphql-tag";
import { Link } from "react-router-dom";
import { GraphQueryInput } from "../GraphQueryInput";
import { filterByQuery, GraphQueryItem } from "../GraphQueryImpl";
import { GaantChart, toGraphQueryItems } from "../gaant/GaantChart";

import { RunStatus } from "../runs/RunUtils";
import styled from "styled-components/macro";
import { Divider, Button, ButtonGroup } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { Line } from "react-chartjs-2";

type Partition = ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet_partitions_results;
type ExecutionPlan = PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan | null;
type Run = PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results;

interface PartitionViewProps extends PartitionPagerProps {
  partitionSet: ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet;
}

export const PartitionView: React.FunctionComponent<PartitionViewProps> = props => {
  const { partitionSet, ...pagerProps } = props;
  const { data }: { data?: PartitionRunsQuery } = useQuery(
    PARTITION_RUNS_QUERY,
    {
      variables: {
        partitionSetName: partitionSet.name
      }
    }
  );
  if (data?.pipelineRunsOrError.__typename !== "PipelineRuns") {
    return null;
  }
  const runs = data.pipelineRunsOrError.results;
  const latestRun = runs[0];
  const executionPlan: ExecutionPlan = latestRun.executionPlan;
  const runsByPartition: { [key: string]: Run[] } = {};
  partitionSet.partitions.results.forEach(
    partition => (runsByPartition[partition.name] = [])
  );
  runs.forEach(run => {
    const tagKV = run.tags.find(tagKV => tagKV.key === "dagster/partition");
    // need to potentially handle un-matched partitions here
    // the current behavior is to just ignore them
    if (runsByPartition[tagKV!.value]) {
      runsByPartition[tagKV!.value].unshift(run); // later runs are from earlier so push them in front
    }
  });

  return (
    <div style={{ marginTop: 30 }}>
      <Header>{`Partition Set: ${partitionSet.name}`}</Header>
      <Divider />
      <PartitionPagerControls {...pagerProps} />
      <PartitionDurationGraph
        partitions={partitionSet.partitions.results}
        runsByPartition={runsByPartition}
        executionPlan={executionPlan}
      />
      <PartitionTable
        runsByPartition={runsByPartition}
        partitions={partitionSet.partitions.results}
      />
    </div>
  );
};

interface LongitudinalPartitionProps {
  partitions: Partition[];
  runsByPartition: { [key: string]: Run[] };
  executionPlan?: ExecutionPlan;
}

const PartitionDurationGraph: React.FunctionComponent<LongitudinalPartitionProps> = ({
  partitions,
  runsByPartition,
  executionPlan
}) => {
  const durationData = _getDurationData(runsByPartition);
  const graph: GraphQueryItem[] = executionPlan
    ? toGraphQueryItems(executionPlan)
    : [];
  const [query, setQuery] = React.useState("*");
  const onUpdateQuery = (query: string) => {
    setQuery(query);
  };
  const chart = React.useRef<Line>(null);

  const selectedSteps = filterByQuery(graph, query).all.map(node => node.name);

  const data = {
    labels: partitions.map(partition => partition.name),
    datasets: Object.keys(durationData)
      .filter(
        label =>
          !query.trim() || query.trim() === "*" || selectedSteps.includes(label)
      )
      .map(label => ({
        label,
        data: durationData[label],
        borderColor: _lineColor(label),
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
        <Line data={data} height={50} ref={chart} />
      </RowContainer>
    </>
  );
};

const _lineColor = (str: string) => {
  let seed = 0;
  for (let i = 0; i < str.length; i++) {
    seed = ((seed << 5) - seed + str.charCodeAt(i)) | 0;
  }

  const random255 = (x: number) => {
    const value = Math.sin(x) * 10000;
    return 255 * (value - Math.floor(value));
  };

  return `rgb(${random255(seed++)}, ${random255(seed++)}, ${random255(
    seed++
  )})`;
};

const _getDurationData = (runsByPartition: { [key: string]: Run[] }) => {
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {};
  Object.keys(runsByPartition).forEach(partitionName => {
    const runs = runsByPartition[partitionName];
    if (!runs || !runs.length) {
      return;
    }
    const { stats, stepStats } = runs[runs.length - 1]; // get most recent run
    const key = "Pipeline Execution Time";
    if (
      stats &&
      stats.__typename === "PipelineRunStatsSnapshot" &&
      stats.endTime &&
      stats.startTime
    ) {
      points[key] = [
        ...(points[key] || []),
        { x: partitionName, y: stats.endTime - stats.startTime }
      ];
    }
    stepStats.forEach(stepStat => {
      if (stepStat.endTime && stepStat.startTime) {
        points[stepStat.stepKey] = [
          ...(points[stepStat.stepKey] || []),
          { x: partitionName, y: stepStat.endTime - stepStat.startTime }
        ];
      }
    });
  });

  return points;
};

const PartitionTable: React.FunctionComponent<LongitudinalPartitionProps> = ({
  runsByPartition
}) => {
  return (
    <>
      {Object.keys(runsByPartition).map(partition => (
        <RowContainer
          key={partition}
          style={{ marginBottom: 0, boxShadow: "none" }}
        >
          <RowColumn>{partition}</RowColumn>
          <RowColumn style={{ textAlign: "left", borderRight: 0 }}>
            {runsByPartition[partition].map(run => (
              <div
                key={run.runId}
                style={{
                  display: "inline-block",
                  cursor: "pointer",
                  marginRight: 5
                }}
              >
                <Link to={`/runs/all/${run.runId}`}>
                  <RunStatus status={run.status} />
                </Link>
              </div>
            ))}
          </RowColumn>
        </RowContainer>
      ))}
    </>
  );
};

export const PARTITION_RUNS_QUERY = gql`
  query PartitionRunsQuery($partitionSetName: String!) {
    pipelineRunsOrError(
      filter: {
        tags: { key: "dagster/partition_set", value: $partitionSetName }
      }
    ) {
      __typename
      ... on PipelineRuns {
        results {
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
            }
          }
          stepStats {
            __typename
            stepKey
            startTime
            endTime
          }
          status
          executionPlan {
            ...GaantChartExecutionPlanFragment
          }
        }
      }
    }
  }
  ${GaantChart.fragments.GaantChartExecutionPlanFragment}
`;

interface PartitionPagerProps {
  displayed: Partition[] | undefined;
  setPageSize: React.Dispatch<React.SetStateAction<number>>;
  hasPrevPage: boolean;
  hasNextPage: boolean;
  cronSchedule: string;
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
