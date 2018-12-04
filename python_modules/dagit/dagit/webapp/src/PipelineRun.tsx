import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import PipelineRunLogMessage from "./PipelineRunLogMessage";
import { IExecutionSessionRun, IExecutionSessionPlan } from "./LocalStorage";
import { PipelineRunLogMessageFragment } from "./types/PipelineRunLogMessageFragment";

interface IPipelineRunProps {
  run: IExecutionSessionRun;
}

interface IPipelineRunExecutionPlanProps {
  executionPlan: IExecutionSessionPlan;
  logs: PipelineRunLogMessageFragment[]; // fix once execution plan view leverages metadata
}

type IStepMetadataState = "waiting" | "running" | "succeeded" | "failed";

interface IStepMetadata {
  state: IStepMetadataState;
  elapsed: number;
}

function stepMetadataFromLogs(
  name: string,
  logs: PipelineRunLogMessageFragment[]
) {
  const START = new RegExp(`Beginning execution of ${name}`);
  const COMPLETION = new RegExp(`Execution of ${name} ([\\w]+) in ([\\d.]+)`);

  const metadata: IStepMetadata = {
    state: "waiting",
    elapsed: 0
  };

  logs.forEach(log => {
    if (START.exec(log.message)) {
      metadata.state = "running";
    }
    let match = COMPLETION.exec(log.message);
    if (match != null) {
      metadata.state = match[1] === "succeeded" ? "succeeded" : "failed";
      metadata.elapsed = Number.parseFloat(match[2]);
    }
  });

  return metadata;
}

class PipelineRunExecutionPlan extends React.Component<
  IPipelineRunExecutionPlanProps
> {
  render() {
    const { executionPlan, logs } = this.props;

    return (
      <ExecutionPlanContainer>
        <ExecutionPlanContainerInner>
          <ExecutionTimeline />
          <ExecutionTimelineMessage>
            <ExecutionTimelineDot /> {logs[0].message}
          </ExecutionTimelineMessage>
          {executionPlan.steps.map(step => {
            const metadata = stepMetadataFromLogs(step.name, logs);
            return (
              <ExecutionPlanBox key={step.name} state={metadata.state}>
                <ExecutionStateDot state={metadata.state} />
                <ExecutionPlanBoxName>{step.name}</ExecutionPlanBoxName>
                {metadata.elapsed > 0 && (
                  <ExecutionStateLabel>
                    {Math.ceil(metadata.elapsed)} sec
                  </ExecutionStateLabel>
                )}
              </ExecutionPlanBox>
            );
          })}
        </ExecutionPlanContainerInner>
      </ExecutionPlanContainer>
    );
  }
}

const ExecutionPlanContainer = styled.div`
  flex: 2;
  overflow-y: scroll;
`;

const ExecutionPlanContainerInner = styled.div`
  margin-top: 15px;
  position: relative;
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  font-size: 0.9em;
`;

const ExecutionPlanBoxName = styled.div`
  font-weight: 500;
`;

const ExecutionPlanBox = styled.div<{ state: IStepMetadataState }>`
  background: ${({ state }) =>
    state === "waiting" ? Colors.GRAY3 : Colors.LIGHT_GRAY2}
  box-shadow: 0 2px 3px rgba(0, 0, 0, 0.3);
  color: ${Colors.DARK_GRAY3};
  padding: 4px;
  padding-right: 10px;
  margin: 6px;
  margin-left: 15px;
  margin-bottom: 0;
  display: inline-flex;
  min-width: 150px;
  align-items: center;
  border-radius: 3px;
  position: relative;
  z-index: 2;
`;

const ExecutionTimelineMessage = styled.div`
  display: flex;
  align-items: center;
  position: relative;
  color: ${Colors.LIGHT_GRAY2};
  z-index: 2;
`;

const ExecutionTimeline = styled.div`
  border-left: 1px solid ${Colors.GRAY3};
  position: absolute;
  top: 10px;
  left: 22px;
  bottom: 10px;
`;

const ExecutionTimelineDot = styled.div`
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 4px;
  margin-right: 8px;
  background: #232b2f;
  border: 1px solid ${Colors.LIGHT_GRAY2};
  margin-left: 18px;
`;

const ExecutionStateDot = styled.div<{ state: IStepMetadataState }>`
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 4px;
  margin-right: 9px;
  background: ${({ state }) =>
    ({
      waiting: Colors.GRAY1,
      running: Colors.GRAY3,
      succeeded: Colors.GREEN2,
      failed: Colors.RED3
    }[state])};
`;

const ExecutionStateLabel = styled.div`
  opacity: 0.7;
  font-size: 0.9em;
  margin-left: 10px;
`;

export class PipelineRun extends React.Component<IPipelineRunProps> {
  render() {
    return (
      <RunContainer>
        <FakeSubscriptionReturningLogs>
          {(logs: PipelineRunLogMessageFragment[]) => (
            <>
              <PipelineRunExecutionPlan
                executionPlan={this.props.run.executionPlan}
                logs={logs}
              />
              <HorizontalDivider />
              <LogsContainer>
                {logs.map((log, i) => (
                  <PipelineRunLogMessage key={i} log={log} />
                ))}
              </LogsContainer>
            </>
          )}
        </FakeSubscriptionReturningLogs>
      </RunContainer>
    );
  }
}

export class PipelineRunEmpty extends React.Component {
  render() {
    return (
      <RunContainer>
        Provide configuration and click the Play icon to execute the pipeline.
      </RunContainer>
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
      "Execution of serialize.load_num_csv.result succeeded in 12.365102767944336"
  },
  {
    __typename: "LogMessageEvent",
    message:
      "Execution of serialize.sum_solid.result succeeded in 12.365102767944336"
  },
  {
    __typename: "LogMessageEvent",
    message:
      "Execution of load_num_csv.transform succeeded in 12.365102767944336"
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
    message: "Execution of sum_sq_solid.transform failed in 5.728006362915039"
  },
  {
    __typename: "PipelineSuccessEvent",
    message: "Completing successful execution of pipeline pandas_hello_world"
  }
];

const FakeSubscriptionReturningLogs = (props: any) => {
  return props.children(FAKE_LOGS);
};

const RunContainer = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1 1;
  color: ${Colors.WHITE};
  border-left: 1px solid ${Colors.DARK_GRAY5};
  background: #232b2f;
`;

const HorizontalDivider = styled.div`
  border-top: 1px solid ${Colors.GRAY4};
  background: ${Colors.GRAY2};
  border-bottom: 1px solid ${Colors.GRAY1};
  display: block;
  height: 3px;
`;
const LogsContainer = styled.div`
  padding-left: 10px;
  padding-top: 5px;
  padding-bottom: 5px;
  display: flex;
  flex: 1 1;
  flex-direction: column;
  overflow-y: scroll;
`;
