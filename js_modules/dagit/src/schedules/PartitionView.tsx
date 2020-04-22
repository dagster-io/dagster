import * as React from "react";

import { Query, QueryResult } from "react-apollo";
import {
  PartitionLongitudinalQuery,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results
} from "./types/PartitionLongitudinalQuery";
import { Header, RowContainer } from "../ListComponents";
import gql from "graphql-tag";

import styled from "styled-components/macro";
import { Divider, Button, ButtonGroup, Spinner } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { Line } from "react-chartjs-2";
import { colorHash } from "../Util";
import Loading from "../Loading";
import { PartitionTable } from "./PartitionTable";

type Partition = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results;

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
                <div
                  style={{
                    position: "relative",
                    maxWidth: 1600,
                    margin: "0 auto"
                  }}
                >
                  <PartitionTable
                    title="Runs by Partition"
                    partitions={partitions}
                  />
                  <PartitionGraph
                    title="Execution Time by Partition"
                    yLabel="Execution time (secs)"
                    partitions={partitions}
                    generateData={_getDurationData}
                  />
                  <PartitionGraph
                    title="Materialization Count by Partition"
                    yLabel="Number of materializations"
                    partitions={partitions}
                    generateData={_getMaterializationData}
                  />
                  <PartitionGraph
                    title="Expectation Successes by Partition"
                    yLabel="Number of successes"
                    partitions={partitions}
                    generateData={_getExpectationsSuccess}
                  />
                  <PartitionGraph
                    title="Expectation Failures by Partition"
                    yLabel="Number of failures"
                    partitions={partitions}
                    generateData={_getExpectationsFailure}
                  />
                  <PartitionGraph
                    title="Expectation Rate by Partition"
                    yLabel="Rate of success"
                    partitions={partitions}
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
  display: flex;
  justify-content: center;
  align-items: center;
`;

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
      y: keyData[partition.name]
    }));
  });

  return points;
};

interface PartitionGraphProps {
  partitions: Partition[];
  generateData: (partitions: Partition[]) => { [key: string]: any };
  title?: string;
  yLabel?: string;
}

const _defaultGraphOptions = (title?: string, yLabel?: string, chart?: any) => {
  const titleOptions = title ? { display: true, text: title } : undefined;
  const scales = yLabel
    ? {
        yAxes: [{ scaleLabel: { display: true, labelString: yLabel } }],
        xAxes: [{ scaleLabel: { display: true, labelString: "Partition" } }]
      }
    : undefined;
  const legend = {
    align: "start",
    position: "right",
    display: true,
    labels: {
      boxWidth: 12
    },
    onClick: (e: MouseEvent, legendItem: any) => {
      const selectedIndex = legendItem.datasetIndex;
      const instance = chart?.current?.chartInstance;
      if (!instance) {
        return;
      }
      const selectedMeta = instance.getDatasetMeta(selectedIndex);

      if (e.shiftKey) {
        // just toggle the selected dataset
        selectedMeta.hidden =
          selectedMeta.hidden === null
            ? !instance.data.datasets[selectedIndex].hidden
            : null;
      } else {
        // only show the selected dataset
        instance.data.datasets.forEach((_: any, i: number) => {
          const meta = instance.getDatasetMeta(i);
          meta.hidden = i !== selectedIndex;
        });
      }

      // rerender the chart
      instance.update();
    }
  };
  return {
    title: titleOptions,
    scales,
    legend
  };
};

const PartitionGraph: React.FunctionComponent<PartitionGraphProps> = ({
  title,
  yLabel,
  partitions,
  generateData
}) => {
  const chart = React.useRef<any>(undefined);
  const data = fillPartitions(generateData(partitions), partitions);
  const graphData = {
    labels: partitions.map(partition => partition.name),
    datasets: Object.keys(data).map(label => ({
      label,
      data: data[label],
      borderColor: colorHash(label),
      backgroundColor: "rgba(0,0,0,0)"
    }))
  };
  const options = _defaultGraphOptions(title, yLabel, chart);
  return (
    <RowContainer style={{ margin: "20px 0" }}>
      <Line data={graphData} height={100} options={options} ref={chart} />
    </RowContainer>
  );
};

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
            }
          }
        }
      }
    }
  }
`;
