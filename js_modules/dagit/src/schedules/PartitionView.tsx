import * as React from "react";

import { Header, RowContainer } from "../ListComponents";
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
import { Divider, Button, ButtonGroup, Menu } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { Line } from "react-chartjs-2";
import { Select, ItemRenderer } from "@blueprintjs/select";

type Partition = ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet_partitions_results;
type ExecutionPlan = PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan | null;
type Run = PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results;

interface PartitionViewProps extends PartitionPagerProps {
  partitionSet: ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet;
}

const VIEW_ITEMS = {
  runs: "Run status by partition",
  duration: "Execution time by partition",
  materializations: "Materializations by partition",
  expectationSuccess: "Expectation successes by partition",
  expectationFailure: "Expectation failures by partition",
  expectationRate: "Expectation rate by partition"
};

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
  const [viewType, setViewType] = React.useState<string>("runs");
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

  const onSelect = (item: string) => {
    setViewType(item);
  };
  const viewTypeRenderer: ItemRenderer<string> = (
    viewType,
    { handleClick, modifiers }
  ) => {
    return (
      <Menu.Item
        active={modifiers.active}
        disabled={modifiers.disabled}
        key={viewType}
        onClick={handleClick}
        text={VIEW_ITEMS[viewType]}
      />
    );
  };

  let partitionView = null;
  if (viewType === "runs") {
    partitionView = <PartitionTable runsByPartition={runsByPartition} />;
  } else if (viewType === "duration") {
    partitionView = (
      <PartitionGraph
        partitions={partitionSet.partitions.results}
        runsByPartition={runsByPartition}
        executionPlan={executionPlan}
        generateData={_getDurationData}
      />
    );
  } else if (viewType === "materializations") {
    partitionView = (
      <PartitionGraph
        partitions={partitionSet.partitions.results}
        runsByPartition={runsByPartition}
        executionPlan={executionPlan}
        generateData={_getMaterializationData}
      />
    );
  } else if (viewType === "expectationSuccess") {
    partitionView = (
      <PartitionGraph
        partitions={partitionSet.partitions.results}
        runsByPartition={runsByPartition}
        executionPlan={executionPlan}
        generateData={_getExpectationsSuccess}
      />
    );
  } else if (viewType === "expectationFailure") {
    partitionView = (
      <PartitionGraph
        partitions={partitionSet.partitions.results}
        runsByPartition={runsByPartition}
        executionPlan={executionPlan}
        generateData={_getExpectationsFailure}
      />
    );
  } else if (viewType === "expectationRate") {
    partitionView = (
      <PartitionGraph
        partitions={partitionSet.partitions.results}
        runsByPartition={runsByPartition}
        executionPlan={executionPlan}
        generateData={_getExpectationsRate}
      />
    );
  }

  return (
    <div style={{ marginTop: 30 }}>
      <Header>{`Partition Set: ${partitionSet.name}`}</Header>
      <Divider />
      <PartitionPagerControls {...pagerProps} />
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          margin: "20px 0px"
        }}
      >
        <Select<string>
          items={Object.keys(VIEW_ITEMS)}
          itemRenderer={viewTypeRenderer}
          onItemSelect={onSelect}
          filterable={false}
        >
          <Button
            text={VIEW_ITEMS[viewType]}
            rightIcon="double-caret-vertical"
            style={{ minWidth: 300 }}
          />
        </Select>
      </div>
      {partitionView}
    </div>
  );
};

interface PartitionGraphProps {
  partitions: Partition[];
  runsByPartition: { [key: string]: Run[] };
  executionPlan?: ExecutionPlan;
  generateData: (runsByPartition: {
    [key: string]: Run[];
  }) => { [key: string]: any };
}

const getLastSuccessfulRunOrLastRun = (runs: Run[]) => {
  const successfulRuns = runs.filter(run => run.status === "SUCCESS");
  return successfulRuns.length
    ? successfulRuns[successfulRuns.length - 1]
    : runs[runs.length - 1];
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
    const { stats, stepStats } = getLastSuccessfulRunOrLastRun(runs);
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

const _getMaterializationData = (runsByPartition: { [key: string]: Run[] }) => {
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {};
  Object.keys(runsByPartition).forEach(partitionName => {
    const runs = runsByPartition[partitionName];
    if (!runs || !runs.length) {
      return;
    }
    const { stats, stepStats } = getLastSuccessfulRunOrLastRun(runs);
    const key = "Total Materializations";
    if (stats && stats.__typename === "PipelineRunStatsSnapshot") {
      points[key] = [
        ...(points[key] || []),
        { x: partitionName, y: stats.materializations }
      ];
    }
    stepStats.forEach(stepStat => {
      points[stepStat.stepKey] = [
        ...(points[stepStat.stepKey] || []),
        { x: partitionName, y: stepStat.materializations?.length || 0 }
      ];
    });
  });

  return points;
};

const _getExpectationsSuccess = (runsByPartition: { [key: string]: Run[] }) => {
  const pipelineKey = "Total Successes";
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {
    [pipelineKey]: []
  };
  Object.keys(runsByPartition).forEach(partitionName => {
    const runs = runsByPartition[partitionName];
    if (!runs || !runs.length) {
      return;
    }
    const { stepStats } = getLastSuccessfulRunOrLastRun(runs);

    let pipelineSuccessCount = 0;
    stepStats.forEach(stepStat => {
      const successCount =
        stepStat.expectationResults?.filter(x => x.success).length || 0;
      points[stepStat.stepKey] = [
        ...(points[stepStat.stepKey] || []),
        {
          x: partitionName,
          y: successCount
        }
      ];
      pipelineSuccessCount += successCount;
    });
    points[pipelineKey] = [
      ...points[pipelineKey],
      { x: partitionName, y: pipelineSuccessCount }
    ];
  });

  return points;
};

const _getExpectationsFailure = (runsByPartition: { [key: string]: Run[] }) => {
  const pipelineKey = "Total Failures";
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {
    [pipelineKey]: []
  };

  Object.keys(runsByPartition).forEach(partitionName => {
    const runs = runsByPartition[partitionName];
    if (!runs || !runs.length) {
      return;
    }
    const { stepStats } = getLastSuccessfulRunOrLastRun(runs);
    let pipelineFailureCount = 0;
    stepStats.forEach(stepStat => {
      const failureCount =
        stepStat.expectationResults?.filter(x => !x.success).length || 0;
      points[stepStat.stepKey] = [
        ...(points[stepStat.stepKey] || []),
        {
          x: partitionName,
          y: failureCount
        }
      ];
      pipelineFailureCount += failureCount;
    });
    points[pipelineKey] = [
      ...points[pipelineKey],
      { x: partitionName, y: pipelineFailureCount }
    ];
  });

  return points;
};

const _getExpectationsRate = (runsByPartition: { [key: string]: Run[] }) => {
  const pipelineKey = "Total Rate";
  const points: {
    [key: string]: { x: string; y: number | null }[];
  } = {
    [pipelineKey]: []
  };
  Object.keys(runsByPartition).forEach(partitionName => {
    const runs = runsByPartition[partitionName];
    if (!runs || !runs.length) {
      return;
    }
    const { stepStats } = getLastSuccessfulRunOrLastRun(runs);
    let pipelineSuccessCount = 0;
    let pipelineTotalCount = 0;
    stepStats.forEach(stepStat => {
      const successCount =
        stepStat.expectationResults?.filter(x => x.success).length || 0;
      const totalCount = stepStat.expectationResults?.length || 0;
      const rate = totalCount ? successCount / totalCount : 0;
      points[stepStat.stepKey] = [
        ...(points[stepStat.stepKey] || []),
        { x: partitionName, y: rate }
      ];
      pipelineSuccessCount += successCount;
      pipelineTotalCount += totalCount;
    });
    points[pipelineKey] = [
      ...points[pipelineKey],
      {
        x: partitionName,
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
  runsByPartition,
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
  const data = fillPartitions(generateData(runsByPartition), partitions);
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
        <Line data={graphData} height={50} />
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

interface PartitionTableProps {
  runsByPartition: { [key: string]: Run[] };
}

const PartitionTable: React.FunctionComponent<PartitionTableProps> = ({
  runsByPartition
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
      {Object.keys(runsByPartition).map(partition => (
        <Column key={partition}>
          <ColumnHeader>{partition}</ColumnHeader>
          {runsByPartition[partition].map(run => (
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
`;
const Column = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column-reverse;
  align-items: stretch;
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
  ${GaantChart.fragments.GaantChartExecutionPlanFragment}
`;
