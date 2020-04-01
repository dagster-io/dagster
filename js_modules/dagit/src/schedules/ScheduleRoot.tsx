import * as React from "react";

import {
  Header,
  ScrollContainer,
  RowColumn,
  RowContainer
} from "../ListComponents";
import { Query, QueryResult, useQuery } from "react-apollo";
import {
  ScheduleRootQuery,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData
} from "./types/ScheduleRootQuery";
import {
  PartitionRunsQuery,
  PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results
} from "./types/PartitionRunsQuery";
import Loading from "../Loading";
import gql from "graphql-tag";
import { RouteComponentProps } from "react-router";
import { Link } from "react-router-dom";
import { ScheduleRow, ScheduleRowFragment, AttemptStatus } from "./ScheduleRow";

import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { showCustomAlert } from "../CustomAlertProvider";
import { unixTimestampToString, assertUnreachable } from "../Util";
import { RunStatus } from "../runs/RunUtils";
import { ScheduleTickStatus } from "../types/globalTypes";
import styled from "styled-components/macro";
import {
  Collapse,
  Divider,
  Icon,
  Intent,
  Callout,
  Code,
  Tag
} from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { Line } from "react-chartjs-2";

import PythonErrorInfo from "../PythonErrorInfo";
import { useState } from "react";

const NUM_RUNS_TO_DISPLAY = 10;
const NUM_ATTEMPTS_TO_DISPLAY = 25;

export class ScheduleRoot extends React.Component<
  RouteComponentProps<{ scheduleName: string }>
> {
  render() {
    const { scheduleName } = this.props.match.params;

    return (
      <Query
        query={SCHEDULE_ROOT_QUERY}
        variables={{
          scheduleName,
          limit: NUM_RUNS_TO_DISPLAY,
          attemptsLimit: NUM_ATTEMPTS_TO_DISPLAY
        }}
        fetchPolicy="cache-and-network"
        pollInterval={15 * 1000}
        partialRefetch={true}
      >
        {(queryResult: QueryResult<ScheduleRootQuery, any>) => (
          <Loading queryResult={queryResult} allowStaleData={true}>
            {result => {
              const { scheduleOrError } = result;

              if (scheduleOrError.__typename === "RunningSchedule") {
                return (
                  <ScrollContainer>
                    <Header>Schedules</Header>
                    <ScheduleRow schedule={scheduleOrError} />
                    <TicksTable ticks={scheduleOrError.ticksList} />
                    <AttemptsTable attemptList={scheduleOrError.attemptList} />
                    {scheduleOrError.scheduleDefinition.partitionSet ? (
                      <PartitionTable
                        partitionSet={
                          scheduleOrError.scheduleDefinition.partitionSet
                        }
                      />
                    ) : null}
                  </ScrollContainer>
                );
              } else {
                return null;
              }
            }}
          </Loading>
        )}
      </Query>
    );
  }
}

const RenderEventSpecificData: React.FunctionComponent<{
  data: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData | null;
}> = ({ data }) => {
  if (!data) {
    return null;
  }

  switch (data.__typename) {
    case "ScheduleTickFailureData":
      return (
        <a
          onClick={() =>
            showCustomAlert({
              title: "Schedule Response",
              body: (
                <>
                  <PythonErrorInfo error={data.error} />
                </>
              )
            })
          }
        >
          <Tag fill={true} minimal={true} intent={Intent.DANGER}>
            See Error
          </Tag>
        </a>
      );
    case "ScheduleTickSuccessData":
      return (
        <a href={`/runs/${data.run?.pipeline.name}/${data.run?.runId}`}>
          <Tag fill={true} minimal={true} intent={Intent.SUCCESS}>
            Run {data.run?.runId}
          </Tag>
        </a>
      );
  }
};

const TickTag: React.FunctionComponent<{ status: ScheduleTickStatus }> = ({
  status
}) => {
  switch (status) {
    case ScheduleTickStatus.STARTED:
      return (
        <Tag minimal={true} intent={Intent.PRIMARY}>
          Success
        </Tag>
      );
    case ScheduleTickStatus.SUCCESS:
      return (
        <Tag minimal={true} intent={Intent.SUCCESS}>
          Success
        </Tag>
      );
    case ScheduleTickStatus.SKIPPED:
      return (
        <Tag minimal={true} intent={Intent.WARNING}>
          Failure
        </Tag>
      );
    case ScheduleTickStatus.FAILURE:
      return (
        <Tag minimal={true} intent={Intent.DANGER}>
          Failure
        </Tag>
      );
    default:
      return assertUnreachable(status);
  }
};

const TicksTable: React.FunctionComponent<{
  ticks: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList[];
}> = ({ ticks }) => {
  return (
    <div style={{ marginTop: 10 }}>
      <Header>Schedule Attempts Log</Header>
      <div>
        {ticks.map((tick, i) => {
          return (
            <RowContainer key={i}>
              <RowColumn>
                {unixTimestampToString(tick.timestamp)}
                <div style={{ marginLeft: 20, display: "inline" }}>
                  <TickTag status={tick.status} />
                </div>
              </RowColumn>
              <RowColumn>
                <RenderEventSpecificData data={tick.tickSpecificData} />
              </RowColumn>
            </RowContainer>
          );
        })}
      </div>
    </div>
  );
};

// TODO: Delete in 0.8.0 release
// https://github.com/dagster-io/dagster/issues/228
interface AttemptsTableProps {
  attemptList: ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList[];
}

const AttemptsTable: React.FunctionComponent<AttemptsTableProps> = ({
  attemptList
}) => {
  const [isOpen, setIsOpen] = useState(false);
  if (!attemptList || !attemptList.length) {
    return null;
  }
  return (
    <AttemptsTableContainer>
      <Header>
        Old Attempts (Deprecated){" "}
        <Icon
          style={{ cursor: "pointer" }}
          icon={isOpen ? IconNames.CHEVRON_DOWN : IconNames.CHEVRON_RIGHT}
          iconSize={Icon.SIZE_LARGE}
          intent={Intent.PRIMARY}
          onClick={() => setIsOpen(!isOpen)}
        />
      </Header>
      <Divider />
      <Collapse isOpen={isOpen}>
        <Callout
          title={
            "These schedule attempts will be no longer visible in Dagit 0.8.0"
          }
          intent={Intent.WARNING}
          style={{ margin: "10px 0" }}
        >
          <p>
            The way Dagster stores schedule attempts has been updated to use a
            database, which can be configured using{" "}
            <a href="https://docs.dagster.io/latest/deploying/instance/#scheduler-storage">
              <Code>Scheduler Storage</Code>
            </a>
            . Previously, attempts were stored on the fileystem at{" "}
            <Code>$DAGSTER_HOME/schedules/logs/</Code>. This update removes the
            dependency on the filesytem for the scheduler, and enables the
            durability of schedule attempt history across deploys of dagster.
          </p>
        </Callout>
        {attemptList.map((attempt, i) => (
          <RowContainer key={i} style={{ marginBottom: 0, boxShadow: "none" }}>
            <RowColumn
              style={{
                maxWidth: 30,
                borderRight: 0,
                padding: 7
              }}
            >
              {attempt.run ? (
                <RunStatus status={attempt.run.status} />
              ) : (
                <AttemptStatus status={attempt.status} />
              )}
            </RowColumn>
            <RowColumn style={{ textAlign: "left", borderRight: 0 }}>
              {attempt.run ? (
                <div>
                  <Link to={`/runs/all/${attempt.run.runId}`}>
                    {attempt.run.runId}
                  </Link>
                </div>
              ) : (
                <div>
                  <ButtonLink
                    onClick={() =>
                      showCustomAlert({
                        title: "Schedule Response",
                        body: (
                          <>
                            <HighlightedCodeBlock
                              value={JSON.stringify(
                                JSON.parse(attempt.jsonResult),
                                null,
                                2
                              )}
                              languages={["json"]}
                            />
                          </>
                        )
                      })
                    }
                  >
                    {" "}
                    View error
                  </ButtonLink>
                </div>
              )}
            </RowColumn>
            <RowColumn
              style={{ maxWidth: 200, paddingLeft: 0, textAlign: "left" }}
            >
              {unixTimestampToString(attempt.time)}
            </RowColumn>
          </RowContainer>
        ))}
      </Collapse>
    </AttemptsTableContainer>
  );
};

const PartitionTable: React.FunctionComponent<{
  partitionSet: ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet;
}> = ({ partitionSet }) => {
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
  const runsByPartition: {
    [key: string]: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results[];
  } = {};
  partitionSet.partitions.forEach(
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

  const latestRunByPartition: {
    [key: string]: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results | null;
  } = {};

  for (const partition in runsByPartition) {
    if (runsByPartition[partition].length > 0) {
      latestRunByPartition[partition] =
        runsByPartition[partition][runsByPartition[partition].length - 1];
    } else {
      latestRunByPartition[partition] = null;
    }
  }

  const pipelineExecutionTimeByPartition: {
    x: string;
    y: number | null;
  }[] = [];
  for (const partition in latestRunByPartition) {
    const latestRun = latestRunByPartition[partition];
    if (!latestRun) {
      pipelineExecutionTimeByPartition.push({
        x: partition,
        y: null
      });
      continue;
    }

    const { stats } = latestRun;
    if (
      stats.__typename == "PipelineRunStatsSnapshot" &&
      stats.endTime &&
      stats.startTime
    ) {
      const duration = stats.endTime - stats.startTime;
      pipelineExecutionTimeByPartition.push({
        x: partition,
        y: duration
      });
    } else {
      pipelineExecutionTimeByPartition.push({
        x: partition,
        y: null
      });
    }
  }

  const state: any = {
    labels: pipelineExecutionTimeByPartition.map(i => i.x),
    datasets: [
      {
        label: "Pipeline Execution Time",
        data: pipelineExecutionTimeByPartition.map(i => i.y)
      }
    ]
  };

  return (
    <>
      <Header>{`Partition Set: ${partitionSet.name}`}</Header>

      <RowContainer style={{ marginBottom: 20 }}>
        <Line data={state} height={50} />
      </RowContainer>
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

export const SCHEDULE_ROOT_QUERY = gql`
  query ScheduleRootQuery(
    $scheduleName: String!
    $limit: Int!
    $attemptsLimit: Int!
  ) {
    scheduleOrError(scheduleName: $scheduleName) {
      ... on RunningSchedule {
        ...ScheduleFragment
        scheduleDefinition {
          name
          partitionSet {
            name
            partitions {
              name
            }
          }
        }
        ticksList: ticks(limit: $attemptsLimit) {
          tickId
          status
          timestamp
          tickSpecificData {
            __typename
            ... on ScheduleTickSuccessData {
              run {
                pipeline {
                  name
                }
                runId
              }
            }
            ... on ScheduleTickFailureData {
              error {
                ...PythonErrorFragment
              }
            }
          }
        }
        attemptList: attempts(limit: $attemptsLimit) {
          time
          jsonResult
          status
          run {
            runId
            status
          }
        }
      }
      ... on ScheduleNotFoundError {
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
  }

  ${ScheduleRowFragment}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
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
            }
          }
          status
        }
      }
    }
  }
`;

const AttemptsTableContainer = styled.div`
  margin: 20px 0;
`;
const ButtonLink = styled.button`
  color: #106ba3;
  margin-left: 10px;
  font-size: 14px;
  background: none !important;
  border: none;
  padding: 0 !important;
  font-family: inherit;
  cursor: pointer;
  &: hover {
    text-decoration: underline;
  }
}
`;
