import * as React from "react";

import {
  Header,
  ScrollContainer,
  RowColumn,
  RowContainer
} from "../ListComponents";
import { Query, QueryResult } from "react-apollo";
import {
  ScheduleRootQuery,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData
} from "./types/ScheduleRootQuery";
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
  Tag,
  AnchorButton
} from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { __RouterContext as RouterContext } from "react-router";
import PythonErrorInfo from "../PythonErrorInfo";
import { useState } from "react";
import * as querystring from "query-string";
import { ButtonLink } from "../ButtonLink";
import { PartitionView } from "./PartitionView";

const NUM_RUNS_TO_DISPLAY = 10;
const NUM_ATTEMPTS_TO_DISPLAY = 25;

export const ScheduleRoot: React.FunctionComponent<RouteComponentProps<{
  scheduleName: string;
}>> = ({ match, location }) => {
  const { scheduleName } = match.params;

  const { history } = React.useContext(RouterContext);
  const qs = querystring.parse(location.search);

  const [cursorStack, setCursorStack] = React.useState<string[]>([]);
  const [pageSize, setPageSize] = React.useState<number>(100);
  const cursor = (qs.cursor as string) || undefined;

  const setCursor = (cursor: string | undefined) => {
    history.push({ search: `?${querystring.stringify({ ...qs, cursor })}` });
  };
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
      query={SCHEDULE_ROOT_QUERY}
      variables={{
        scheduleName,
        limit: NUM_RUNS_TO_DISPLAY,
        attemptsLimit: NUM_ATTEMPTS_TO_DISPLAY,
        partitionsCursor: cursor,
        partitionsLimit: pageSize + 1
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
              const partitionSet =
                scheduleOrError.scheduleDefinition.partitionSet;
              const displayed = partitionSet?.partitions.results.slice(
                0,
                pageSize
              );
              const hasPrevPage = !!cursor;
              const hasNextPage =
                partitionSet?.partitions.results.length === pageSize + 1;

              return (
                <ScrollContainer>
                  <Header>Schedules</Header>
                  <ScheduleRow schedule={scheduleOrError} />
                  <TicksTable ticks={scheduleOrError.ticksList} />
                  <AttemptsTable attemptList={scheduleOrError.attemptList} />
                  {scheduleOrError.scheduleDefinition.partitionSet ? (
                    <PartitionView
                      cronSchedule={
                        scheduleOrError.scheduleDefinition.cronSchedule
                      }
                      partitionSet={
                        scheduleOrError.scheduleDefinition.partitionSet
                      }
                      displayed={displayed}
                      setPageSize={setPageSize}
                      hasPrevPage={hasPrevPage}
                      hasNextPage={hasNextPage}
                      pushCursor={pushCursor}
                      popCursor={popCursor}
                      setCursor={setCursor}
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
};

const RenderEventSpecificData: React.FunctionComponent<{
  data: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData | null;
}> = ({ data }) => {
  if (!data) {
    return null;
  }

  switch (data.__typename) {
    case "ScheduleTickFailureData":
      return (
        <AnchorButton
          minimal={true}
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
        </AnchorButton>
      );
    case "ScheduleTickSuccessData":
      return (
        <AnchorButton
          minimal={true}
          href={`/runs/${data.run?.pipeline.name}/${data.run?.runId}`}
        >
          <Tag fill={true} minimal={true} intent={Intent.SUCCESS}>
            Run {data.run?.runId}
          </Tag>
        </AnchorButton>
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
  return ticks && ticks.length ? (
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
  ) : null;
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

export const SCHEDULE_ROOT_QUERY = gql`
  query ScheduleRootQuery(
    $scheduleName: String!
    $limit: Int!
    $attemptsLimit: Int!
    $partitionsLimit: Int
    $partitionsCursor: String
  ) {
    scheduleOrError(scheduleName: $scheduleName) {
      ... on RunningSchedule {
        ...ScheduleFragment
        scheduleDefinition {
          name
          cronSchedule
          partitionSet {
            name
            partitions(cursor: $partitionsCursor, limit: $partitionsLimit) {
              results {
                name
              }
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

const AttemptsTableContainer = styled.div`
  margin: 20px 0;
`;
