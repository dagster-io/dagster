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
  ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList
} from "./types/ScheduleRootQuery";
import Loading from "../Loading";
import gql from "graphql-tag";
import { match } from "react-router";
import { Link } from "react-router-dom";
import { ScheduleRow, ScheduleRowFragment, AttemptStatus } from "./ScheduleRow";

import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { showCustomAlert } from "../CustomAlertProvider";
import { unixTimestampToString } from "../Util";
import { RunStatus } from "../runs/RunUtils";

const NUM_RUNS_TO_DISPLAY = 10;
const NUM_ATTEMPTS_TO_DISPLAY = 25;

interface IScheduleRootProps {
  match: match<{ scheduleName: string }>;
}

export class ScheduleRoot extends React.Component<IScheduleRootProps> {
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
          <Loading queryResult={queryResult}>
            {result => {
              const { scheduleOrError } = result;

              if (scheduleOrError.__typename === "RunningSchedule") {
                return (
                  <ScrollContainer>
                    <Header>Schedule</Header>
                    <ScheduleRow schedule={scheduleOrError} />
                    <AttemptsTable attemptList={scheduleOrError.attemptList} />
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
    <>
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
                <Link to={`/runs/${attempt.run.runId}`}>
                  {attempt.run.runId}
                </Link>
              </div>
            ) : (
              <div>
                <a
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
                </a>
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
        id
        scheduleDefinition {
          name
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
