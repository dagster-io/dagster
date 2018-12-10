import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import PipelineRunExecutionPlan from "./PipelineRunExecutionPlan";
import PipelineRunLogMessage from "./PipelineRunLogMessage";
import { PipelineRunFragment } from "./types/PipelineRunFragment";

interface IPipelineRunProps {
  pipelineRun: PipelineRunFragment;
}

export class PipelineRun extends React.Component<IPipelineRunProps> {
  static fragments = {
    PipelineRunFragment: gql`
      fragment PipelineRunFragment on PipelineRun {
        logs {
          nodes {
            ...PipelineRunLogMessageFragment
          }
        }
        ...PipelineRunExecutionPlanFragment
      }

      ${PipelineRunExecutionPlan.fragments.PipelineRunExecutionPlanFragment}
      ${PipelineRunLogMessage.fragments.PipelineRunLogMessageFragment}
    `,
    PipelineRunPipelineRunEventFragment: gql`
      fragment PipelineRunPipelineRunEventFragment on PipelineRunEvent {
        ...PipelineRunLogMessageFragment
        ...PipelineRunExecutionPlanPipelineRunEventFragment
      }

      ${PipelineRunExecutionPlan.fragments
        .PipelineRunExecutionPlanPipelineRunEventFragment}
      ${PipelineRunLogMessage.fragments.PipelineRunLogMessageFragment}
    `
  };
  render() {
    return (
      <PipelineRunWrapper>
        <PipelineRunExecutionPlan pipelineRun={this.props.pipelineRun} />
        <HorizontalDivider />
        <LogsContainer>
          {this.props.pipelineRun.logs.nodes.map((log, i) => (
            <PipelineRunLogMessage key={i} log={log} />
          ))}
        </LogsContainer>
      </PipelineRunWrapper>
    );
  }
}

export class PipelineRunEmpty extends React.Component {
  render() {
    return (
      <PipelineRunWrapper>
        Provide configuration and click the Play icon to execute the pipeline.
      </PipelineRunWrapper>
    );
  }
}

const PipelineRunWrapper = styled.div`
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
