import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import PipelineRunLogMessage from "./PipelineRunLogMessage";
import { IExecutionSessionRun } from "./LocalStorage";
import { PipelineRunLogMessageFragment } from "./types/PipelineRunLogMessageFragment";

interface IPipelineRunProps {
  run: IExecutionSessionRun;
}

const PipelineRunLogsContainer = styled.div`
  padding-left: 35px;
  padding-top: 5px;
  padding-bottom: 5px;
  display: flex;
  flex: 1 1;
  flex-direction: column;
`;

export default class PipelineRun extends React.Component<IPipelineRunProps> {
  static Empty = PipelineRunLogsContainer;

  render() {
    return (
      <PipelineRunLogsContainer>
        <FakeSubscriptionReturningLogs>
          {(logs: PipelineRunLogMessageFragment[]) => (
            <>
              {logs.map((log, i) => (
                <PipelineRunLogMessage key={i} log={log} />
              ))}
            </>
          )}
        </FakeSubscriptionReturningLogs>
      </PipelineRunLogsContainer>
    );
  }
}

const FAKE_LOGS: PipelineRunLogMessageFragment[] = [
  {
    __typename: "PipelineStartEvent",
    message: "Beginning execution of pipeline pandas_hello_world"
  },
  {
    __typename: "LogMessageEvent",
    message:
      "About to execute the compute node graph in the following order ['load_num_csv.transform', 'sum_solid.transform', 'sum_sq_solid.transform']"
  },
  {
    __typename: "LogMessageEvent",
    message:
      "Entering execute_steps loop. Order: ['load_num_csv.transform', 'sum_solid.transform', 'sum_sq_solid.transform']"
  },
  {
    __typename: "LogMessageEvent",
    message: "Beginning execution of load_num_csv.transform"
  },
  {
    __typename: "LogMessageEvent",
    message: "Executing core transform for solid load_num_csv."
  },
  {
    __typename: "LogMessageEvent",
    message:
      'Solid load_num_csv emitted output "result" value    num1  num2\n0     1     2\n1     3     4'
  },
  {
    __typename: "LogMessageEvent",
    message:
      "Execution of load_num_csv.transform succeeded in 12.365102767944336"
  },
  {
    __typename: "LogMessageEvent",
    message: "Beginning execution of sum_solid.transform"
  },
  {
    __typename: "LogMessageEvent",
    message: "Executing core transform for solid sum_solid."
  },
  {
    __typename: "LogMessageEvent",
    message:
      'Solid sum_solid emitted output "result" value    num1  num2  sum\n0     1     2    3\n1     3     4    7'
  },
  {
    __typename: "LogMessageEvent",
    message: "Execution of sum_solid.transform succeeded in 6.067037582397461"
  },
  {
    __typename: "LogMessageEvent",
    message: "Beginning execution of sum_sq_solid.transform"
  },
  {
    __typename: "LogMessageEvent",
    message: "Executing core transform for solid sum_sq_solid."
  },
  {
    __typename: "LogMessageEvent",
    message:
      'Solid sum_sq_solid emitted output "result" value    num1  num2  sum  sum_sq\n0     1     2    3       9\n1     3     4    7      49'
  },
  {
    __typename: "LogMessageEvent",
    message:
      "Execution of sum_sq_solid.transform succeeded in 5.728006362915039"
  },
  {
    __typename: "PipelineSuccessEvent",
    message: "Completing successful execution of pipeline pandas_hello_world"
  }
];

const FakeSubscriptionReturningLogs = (props: any) => {
  return props.children(FAKE_LOGS);
};
