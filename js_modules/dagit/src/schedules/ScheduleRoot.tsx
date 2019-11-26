import * as React from "react";

import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { Header, ScrollContainer } from "../ListComponents";
import { Query, QueryResult } from "react-apollo";
import {
  ScheduleRootQuery,
  ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList
} from "./types/ScheduleRootQuery";
import Loading from "../Loading";
import gql from "graphql-tag";
import { match } from "react-router";
import ScheduleRow, { ScheduleRowFragment } from "./ScheduleRow";

import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { showCustomAlert } from "../CustomAlertProvider";
import { unixTimestampToString } from "../Util";
import { ScheduleAttemptStatus } from "../types/globalTypes";

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
  return (
    <>
      <Header>Attempts</Header>
      {attemptList.map((attempt, i) => (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            backgroundColor: "white",
            padding: "5px 10px",
            margin: "4px 0"
          }}
          key={i}
        >
          <AttemptStatus status={attempt.status} />
          <AttemptMessage result={attempt.jsonResult} />
          {unixTimestampToString(attempt.time)}
        </div>
      ))}
    </>
  );
};

export const Link = styled.a`
  color: ${Colors.DARK_GRAY4};
  text-decoration: underline;
  margin-left: 10px;
`;

const AttemptMessage = ({ result }: { result: string }) => {
  return (
    <div>
      <Link
        onClick={() =>
          showCustomAlert({
            body: (
              <>
                <HighlightedCodeBlock
                  value={JSON.stringify(JSON.parse(result), null, 2)}
                  languages={["json"]}
                />
              </>
            )
          })
        }
      >
        View Response
      </Link>
    </div>
  );
};

const AttemptStatus = styled.div<{ status: ScheduleAttemptStatus }>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  align-self: center;
  transition: background 200ms linear;
  background: ${({ status }) =>
    ({
      [ScheduleAttemptStatus.SUCCESS]: Colors.GREEN2,
      [ScheduleAttemptStatus.ERROR]: Colors.RED3,
      [ScheduleAttemptStatus.SKIPPED]: Colors.GOLD3
    }[status])};
  &:hover {
    background: ${({ status }) =>
      ({
        [ScheduleAttemptStatus.SUCCESS]: Colors.GREEN2,
        [ScheduleAttemptStatus.ERROR]: Colors.RED3,
        [ScheduleAttemptStatus.SKIPPED]: Colors.GOLD3
      }[status])};
  }
`;

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
