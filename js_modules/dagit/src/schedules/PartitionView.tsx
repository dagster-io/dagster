import * as React from "react";

import { Query, QueryResult } from "react-apollo";
import {
  PartitionLongitudinalQuery,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs
} from "./types/PartitionLongitudinalQuery";
import { Header } from "../ListComponents";
import gql from "graphql-tag";

import styled from "styled-components/macro";
import { Divider, Button, ButtonGroup, Spinner } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import Loading from "../Loading";
import { PartitionTable } from "./PartitionTable";
import { PartitionGraph, PIPELINE_LABEL } from "./PartitionGraph";
import { PartitionRunMatrix } from "./PartitionRunMatrix";
import { colorHash } from "../Util";
import { Colors } from "@blueprintjs/core";
import { RunsFilter } from "../runs/RunsFilter";
import { TokenizingFieldValue } from "../TokenizingField";
import { useRepositorySelector } from "../DagsterRepositoryContext";
import PythonErrorInfo from "../PythonErrorInfo";
import { RunTable } from "../runs/RunTable";

type Partition = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results;
type Run = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs;

interface PartitionViewProps {
  pipelineName: string;
  partitionSetName: string;
  cursor: string | undefined;
  setCursor: (cursor: string | undefined) => void;
}

export const PartitionView: React.FunctionComponent<PartitionViewProps> = ({
  pipelineName,
  partitionSetName,
  cursor,
  setCursor
}) => {
  const [cursorStack, setCursorStack] = React.useState<string[]>([]);
  const [pageSize, setPageSize] = React.useState<number | undefined>(30);
  const repositorySelector = useRepositorySelector();
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
        repositorySelector,
        partitionsCursor: cursor,
        partitionsLimit: pageSize,
        reverse: true
      }}
      fetchPolicy="cache-and-network"
      pollInterval={15 * 1000}
      partialRefetch={true}
    >
      {(queryResult: QueryResult<PartitionLongitudinalQuery, any>) => (
        <Loading queryResult={queryResult} allowStaleData={true}>
          {({ partitionSetOrError }) => {
            if (partitionSetOrError.__typename !== "PartitionSet") {
              return null;
            }
            const partitionSet = partitionSetOrError;
            const partitions =
              partitionSet.partitionsOrError.__typename === "Partitions"
                ? partitionSet.partitionsOrError.results
                : [];
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
            const showLoading = queryResult.loading && queryResult.networkStatus !== 6;
            return (
              <div style={{ marginTop: 30 }}>
                <Header>{`Partition Set: ${partitionSetName}`}</Header>
                <Divider />
                <PartitionPagerControls
                  displayed={partitions.slice(0, pageSize)}
                  pageSize={pageSize}
                  setPageSize={setPageSize}
                  hasNextPage={!!cursor}
                  hasPrevPage={partitions.length === pageSize}
                  pushCursor={pushCursor}
                  popCursor={popCursor}
                  setCursor={setCursor}
                />
                <div style={{ position: "relative" }}>
                  <PartitionRunMatrix pipelineName={pipelineName} partitions={partitions} />
                  <PartitionContent
                    partitions={partitions}
                    allStepKeys={Object.keys(allStepKeys)}
                  />
                  {showLoading && (
                    <Overlay>
                      <Spinner size={48} />
                    </Overlay>
                  )}
                </div>
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
  allStepKeys
}: {
  partitions: Partition[];
  allStepKeys: string[];
}) => {
  const initial: { [stepKey: string]: boolean } = { [PIPELINE_LABEL]: true };
  allStepKeys.forEach(stepKey => (initial[stepKey] = true));
  const [selectedStepKeys, setSelectedStepKeys] = React.useState(initial);
  const [tokens, setTokens] = React.useState<TokenizingFieldValue[]>([]);
  const durationGraph = React.useRef<any>(undefined);
  const materializationGraph = React.useRef<any>(undefined);
  const successGraph = React.useRef<any>(undefined);
  const failureGraph = React.useRef<any>(undefined);
  const rateGraph = React.useRef<any>(undefined);
  const graphs = [durationGraph, materializationGraph, successGraph, failureGraph, rateGraph];

  const onStepChange = (selectedKeys: { [stepKey: string]: boolean }) => {
    setSelectedStepKeys(selectedKeys);
    graphs.forEach(graph => {
      const chart = graph?.current?.chart?.current?.chartInstance;
      const datasets = chart?.data?.datasets || [];
      datasets.forEach((dataset: any, idx: number) => {
        const meta = chart.getDatasetMeta(idx);
        meta.hidden = dataset.label in selectedKeys ? !selectedKeys[dataset.label] : false;
      });
    });
  };

  const runsByPartitionName = {};
  partitions.forEach(partition => {
    runsByPartitionName[partition.name] = partition.runs.filter(
      run => !tokens.length || tokens.every(token => applyFilter(token, run))
    );
  });

  return (
    <PartitionContentContainer>
      <div style={{ flex: 1 }}>
        <PartitionTable title="Runs by Partition" runsByPartitionName={runsByPartitionName} />
        <PartitionGraph
          title="Execution Time by Partition"
          yLabel="Execution time (secs)"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineDurationForRun}
          getStepDataForRun={getStepDurationsForRun}
          ref={durationGraph}
        />
        <PartitionGraph
          title="Materialization Count by Partition"
          yLabel="Number of materializations"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineMaterializationCountForRun}
          getStepDataForRun={getStepMaterializationCountForRun}
          ref={materializationGraph}
        />
        <PartitionGraph
          title="Expectation Successes by Partition"
          yLabel="Number of successes"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationSuccessForRun}
          getStepDataForRun={getStepExpectationSuccessForRun}
          ref={successGraph}
        />
        <PartitionGraph
          title="Expectation Failures by Partition"
          yLabel="Number of failures"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationFailureForRun}
          getStepDataForRun={getStepExpectationFailureForRun}
          ref={failureGraph}
        />
        <PartitionGraph
          title="Expectation Rate by Partition"
          yLabel="Rate of success"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationiRateForRun}
          getStepDataForRun={getStepExpectationRateForRun}
          ref={rateGraph}
        />
      </div>
      <div style={{ width: 450 }}>
        <NavContainer>
          <NavSectionHeader>Run filters</NavSectionHeader>
          <NavSection>
            <RunsFilter tokens={tokens} onChange={setTokens} enabledFilters={["status", "tag"]} />
          </NavSection>
          <StepSelector selected={selectedStepKeys} onChange={onStepChange} />
        </NavContainer>
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
    <>
      <NavSectionHeader>
        Run steps
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: 13, opacity: 0.5 }}>Tip: Shift-click to multi-select</span>
      </NavSectionHeader>
      <NavSection>
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
      </NavSection>
    </>
  );
};

const NavSectionHeader = styled.div`
  border-bottom: 1px solid ${Colors.GRAY5};
  margin-bottom: 10px;
  padding-bottom: 5px;
  display: flex;
`;
const NavSection = styled.div`
  margin-bottom: 30px;
`;
const NavContainer = styled.div`
  margin: 20px 0 0 10px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid ${Colors.GRAY5};
  overflow: auto;
`;

const Item = styled.div`
  list-style-type: none;
  padding: 5px 2px;
  cursor: pointer;
  text-decoration: ${({ shown }: { shown: boolean }) => (shown ? "none" : "line-through")};
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
  z-index: 1000;
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
  const stepCounts: { [key: string]: number } = getStepExpectationSuccessForRun(run);
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
  const stepCounts: { [key: string]: number } = getStepExpectationFailureForRun(run);
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

const applyFilter = (filter: TokenizingFieldValue, run: Run) => {
  if (filter.token === "id") {
    return run.runId === filter.value;
  }
  if (filter.token === "status") {
    return run.status === filter.value;
  }
  if (filter.token === "tag") {
    return run.tags.some(tag => filter.value === `${tag.key}=${tag.value}`);
  }
  return true;
};

interface PartitionPagerProps {
  displayed: Partition[];
  pageSize: number | undefined;
  setPageSize: React.Dispatch<React.SetStateAction<number | undefined>>;
  hasPrevPage: boolean;
  hasNextPage: boolean;
  pushCursor: (nextCursor: string) => void;
  popCursor: () => void;
  setCursor: (cursor: string | undefined) => void;
}

const PartitionPagerControls: React.FunctionComponent<PartitionPagerProps> = ({
  displayed,
  pageSize,
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
        {[7, 30, 120].map(size => (
          <Button
            key={size}
            active={!hasNextPage && pageSize === size}
            onClick={() => {
              setCursor(undefined);
              setPageSize(size);
            }}
          >
            Last {size}
          </Button>
        ))}
        <Button
          active={pageSize === undefined}
          onClick={() => {
            setCursor(undefined);
            setPageSize(undefined);
          }}
        >
          All
        </Button>
      </ButtonGroup>

      <ButtonGroup>
        <Button
          disabled={!hasPrevPage}
          icon={IconNames.ARROW_LEFT}
          onClick={() => displayed && pushCursor(displayed[0].name)}
        >
          Back
        </Button>
        <Button
          disabled={!hasNextPage}
          rightIcon={IconNames.ARROW_RIGHT}
          onClick={() => popCursor()}
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
    $repositorySelector: RepositorySelector!
    $partitionsLimit: Int
    $partitionsCursor: String
    $reverse: Boolean
  ) {
    partitionSetOrError(
      repositorySelector: $repositorySelector
      partitionSetName: $partitionSetName
    ) {
      ... on PartitionSet {
        name
        partitionsOrError(cursor: $partitionsCursor, limit: $partitionsLimit, reverse: $reverse) {
          ... on Partitions {
            results {
              name
              runs {
                runId
                pipelineName
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
                status
                stepStats {
                  __typename
                  stepKey
                  startTime
                  endTime
                  status
                  materializations {
                    __typename
                  }
                  expectationResults {
                    success
                  }
                }
                ...RunTableRunFragment
              }
            }
          }
          ... on PythonError {
            ...PythonErrorFragment
          }
        }
      }
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${RunTable.fragments.RunTableRunFragment}
`;
