import * as React from "react";

import { Query, QueryResult } from "react-apollo";
import {
  PartitionLongitudinalQuery,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs
} from "./types/PartitionLongitudinalQuery";
import { Header } from "../ListComponents";
import gql from "graphql-tag";

import styled from "styled-components/macro";
import { Divider, Button, ButtonGroup, Spinner } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import Loading from "../Loading";
import { PartitionTable } from "./PartitionTable";
import { PartitionGraph, PIPELINE_LABEL } from "./PartitionGraph";
import { colorHash } from "../Util";
import { Colors } from "@blueprintjs/core";

type Partition = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results;
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
            const allStepKeys = {};
            partitions.forEach(partition => {
              partition.runs?.forEach(run => {
                if (!run) {
                  return;
                }
                run.stepStats.forEach(stat => {
                  allStepKeys[stat.stepKey] = true;
                });
              });
            });

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
                <PartitionContent
                  partitions={partitions}
                  loading={queryResult.loading}
                  allStepKeys={Object.keys(allStepKeys)}
                />
              </div>
            );
          }}
        </Loading>
      )}
    </Query>
  );
};

const PartitionContent = ({
  partitions,
  allStepKeys,
  loading
}: {
  partitions: Partition[];
  allStepKeys: string[];
  loading: boolean;
}) => {
  const initial: { [stepKey: string]: boolean } = { [PIPELINE_LABEL]: true };
  allStepKeys.forEach(stepKey => (initial[stepKey] = true));
  const [selectedStepKeys, setSelectedStepKeys] = React.useState(initial);
  const durationGraph = React.useRef<any>(undefined);
  const materializationGraph = React.useRef<any>(undefined);
  const successGraph = React.useRef<any>(undefined);
  const failureGraph = React.useRef<any>(undefined);
  const rateGraph = React.useRef<any>(undefined);
  const graphs = [
    durationGraph,
    materializationGraph,
    successGraph,
    failureGraph,
    rateGraph
  ];

  const onStepChange = (selectedKeys: { [stepKey: string]: boolean }) => {
    setSelectedStepKeys(selectedKeys);
    graphs.forEach(graph => {
      const chart = graph?.current?.chart?.current?.chartInstance;
      const datasets = chart?.data?.datasets || [];
      datasets.forEach((dataset: any, idx: number) => {
        const meta = chart.getDatasetMeta(idx);
        meta.hidden =
          dataset.label in selectedKeys ? !selectedKeys[dataset.label] : false;
      });
    });
  };

  return (
    <PartitionContentContainer>
      <div style={{ flex: 1 }}>
        <PartitionTable title="Runs by Partition" partitions={partitions} />
        <PartitionGraph
          title="Execution Time by Partition"
          yLabel="Execution time (secs)"
          partitions={partitions}
          getPipelineDataForRun={getPipelineDurationForRun}
          getStepDataForRun={getStepDurationsForRun}
          ref={durationGraph}
        />
        <PartitionGraph
          title="Materialization Count by Partition"
          yLabel="Number of materializations"
          partitions={partitions}
          getPipelineDataForRun={getPipelineMaterializationCountForRun}
          getStepDataForRun={getStepMaterializationCountForRun}
          ref={materializationGraph}
        />
        <PartitionGraph
          title="Expectation Successes by Partition"
          yLabel="Number of successes"
          partitions={partitions}
          getPipelineDataForRun={getPipelineExpectationSuccessForRun}
          getStepDataForRun={getStepExpectationSuccessForRun}
          ref={successGraph}
        />
        <PartitionGraph
          title="Expectation Failures by Partition"
          yLabel="Number of failures"
          partitions={partitions}
          getPipelineDataForRun={getPipelineExpectationFailureForRun}
          getStepDataForRun={getStepExpectationFailureForRun}
          ref={failureGraph}
        />
        <PartitionGraph
          title="Expectation Rate by Partition"
          yLabel="Rate of success"
          partitions={partitions}
          getPipelineDataForRun={getPipelineExpectationiRateForRun}
          getStepDataForRun={getStepExpectationRateForRun}
          ref={rateGraph}
        />
      </div>
      {loading ? (
        <Overlay>
          <Spinner size={48} />
        </Overlay>
      ) : null}
      <div style={{ width: 400 }}>
        <StepSelector selected={selectedStepKeys} onChange={onStepChange} />
      </div>
    </PartitionContentContainer>
  );
};

const StepSelector = ({
  selected,
  onChange
}: {
  selected: { [stepKey: string]: boolean };
  onChange: (selected: { [stepKey: string]: boolean }) => void;
}) => {
  const onStepClick = (stepKey: string) => {
    return (evt: React.MouseEvent) => {
      if (evt.shiftKey) {
        // toggle on shift+click
        onChange({ ...selected, [stepKey]: !selected[stepKey] });
      } else {
        // regular click
        const newSelected = {};

        const alreadySelected = Object.keys(selected).every(key => {
          return key === stepKey ? selected[key] : !selected[key];
        });

        Object.keys(selected).forEach(key => {
          newSelected[key] = alreadySelected || key === stepKey;
        });

        onChange(newSelected);
      }
    };
  };

  return (
    <NavContainer>
      {Object.keys(selected).map(stepKey => (
        <Item
          key={stepKey}
          shown={selected[stepKey]}
          onClick={onStepClick(stepKey)}
          color={stepKey === PIPELINE_LABEL ? Colors.GRAY2 : colorHash(stepKey)}
        >
          <div
            style={{
              display: "inline-block",
              marginRight: 5,
              borderRadius: 5,
              height: 10,
              width: 10,
              backgroundColor: selected[stepKey]
                ? stepKey === PIPELINE_LABEL
                  ? Colors.GRAY2
                  : colorHash(stepKey)
                : "#aaaaaa"
            }}
          />
          {stepKey}
        </Item>
      ))}
    </NavContainer>
  );
};

const NavContainer = styled.ul`
  margin: 20px 10px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid #ececec;
  overflow: auto;
`;

const Item = styled.li`
  list-style-type: none;
  padding: 5px 2px;
  cursor: pointer;
  text-decoration: ${({ shown }: { shown: boolean }) =>
    shown ? "none" : "line-through"};
  user-select: none;
  font-size: 12px;
  color: ${props => (props.shown ? props.color : "#aaaaaa")};
  white-space: nowrap;
`;
const PartitionContentContainer = styled.div`
  display: flex;
  flex-direction: row;
  position: relative;
  max-width: 1600px;
  margin: 0 auto;
`;

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

const getPipelineDurationForRun = (run: Run) => {
  const { stats } = run;
  if (
    stats &&
    stats.__typename === "PipelineRunStatsSnapshot" &&
    stats.endTime &&
    stats.startTime
  ) {
    return stats.endTime - stats.startTime;
  }

  return undefined;
};

const getStepDurationsForRun = (run: Run) => {
  const { stepStats } = run;

  const perStepDuration = {};
  stepStats.forEach(stepStat => {
    if (stepStat.endTime && stepStat.startTime) {
      perStepDuration[stepStat.stepKey] = stepStat.endTime - stepStat.startTime;
    }
  });

  return perStepDuration;
};

const getPipelineMaterializationCountForRun = (run: Run) => {
  const { stats } = run;
  if (stats && stats.__typename === "PipelineRunStatsSnapshot") {
    return stats.materializations;
  }
  return undefined;
};

const getStepMaterializationCountForRun = (run: Run) => {
  const { stepStats } = run;
  const perStepCounts = {};
  stepStats.forEach(stepStat => {
    perStepCounts[stepStat.stepKey] = stepStat.materializations?.length || 0;
  });
  return perStepCounts;
};

const getPipelineExpectationSuccessForRun = (run: Run) => {
  const stepCounts: { [key: string]: number } = getStepExpectationSuccessForRun(
    run
  );
  return _arraySum(Object.values(stepCounts));
};

const getStepExpectationSuccessForRun = (run: Run) => {
  const { stepStats } = run;
  const perStepCounts = {};
  stepStats.forEach(stepStat => {
    perStepCounts[stepStat.stepKey] =
      stepStat.expectationResults?.filter(x => x.success).length || 0;
  });
  return perStepCounts;
};

const getPipelineExpectationFailureForRun = (run: Run) => {
  const stepCounts: { [key: string]: number } = getStepExpectationFailureForRun(
    run
  );
  return _arraySum(Object.values(stepCounts));
};

const getStepExpectationFailureForRun = (run: Run) => {
  const { stepStats } = run;
  const perStepCounts = {};
  stepStats.forEach(stepStat => {
    perStepCounts[stepStat.stepKey] =
      stepStat.expectationResults?.filter(x => !x.success).length || 0;
  });
  return perStepCounts;
};

const _arraySum = (arr: number[]) => {
  let sum = 0;
  arr.forEach(x => (sum += x));
  return sum;
};

const getPipelineExpectationiRateForRun = (run: Run) => {
  const stepSuccesses: {
    [key: string]: number;
  } = getStepExpectationSuccessForRun(run);
  const stepFailures: {
    [key: string]: number;
  } = getStepExpectationFailureForRun(run);

  const pipelineSuccesses = _arraySum(Object.values(stepSuccesses));
  const pipelineFailures = _arraySum(Object.values(stepFailures));
  const pipelineTotal = pipelineSuccesses + pipelineFailures;

  return pipelineTotal ? pipelineSuccesses / pipelineTotal : 0;
};

const getStepExpectationRateForRun = (run: Run) => {
  const { stepStats } = run;
  const perStepCounts = {};
  stepStats.forEach(stepStat => {
    const results = stepStat.expectationResults || [];
    perStepCounts[stepStat.stepKey] = results.length
      ? results.filter(x => x.success).length / results.length
      : 0;
  });
  return perStepCounts;
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
