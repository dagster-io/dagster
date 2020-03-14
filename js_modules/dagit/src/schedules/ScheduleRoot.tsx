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
  ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet
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
import { unixTimestampToString } from "../Util";
import { RunStatus } from "../runs/RunUtils";
import styled from "styled-components/macro";

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

interface AttemptsTableProps {
  attemptList: ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList[];
}

const AttemptsTable: React.FunctionComponent<AttemptsTableProps> = ({
  attemptList
}) => {
  if (!attemptList || !attemptList.length) {
    return null;
  }
  return (
    <div style={{ marginBottom: 9 }}>
      <Header>Attempts</Header>
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
                  View response
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
    </div>
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
    // need to defend against mis match in partitions here
    runsByPartition[tagKV!.value].unshift(run); // later runs are from earlier so push them in front
  });

  return (
    <>
      <Header>{`Partition Set: ${partitionSet.name}`}</Header>
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
          status
        }
      }
    }
  }
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
