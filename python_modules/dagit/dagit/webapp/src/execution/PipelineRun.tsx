import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Button, InputGroup } from "@blueprintjs/core";
import PipelineRunExecutionPlan from "./PipelineRunExecutionPlan";
import { PipelineRunFragment } from "./types/PipelineRunFragment";
import { PanelDivider } from "../PanelDivider";
import PipelineRunFilteredLogs from "./PipelineRunFilteredLogs";

interface IPipelineRunProps {
  pipelineRun: PipelineRunFragment;
}

interface IPipelineRunState {
  logsVH: number;
  logsFilter: string;
}

export class PipelineRun extends React.Component<
  IPipelineRunProps,
  IPipelineRunState
> {
  static fragments = {
    PipelineRunFragment: gql`
      fragment PipelineRunFragment on PipelineRun {
        logs {
          nodes {
            ...PipelineRunFilteredLogMessageFragment
          }
        }
        ...PipelineRunExecutionPlanFragment
      }

      ${PipelineRunExecutionPlan.fragments.PipelineRunExecutionPlanFragment}
      ${PipelineRunFilteredLogs.fragments.PipelineRunFilteredLogMessageFragment}
    `,
    PipelineRunPipelineRunEventFragment: gql`
      fragment PipelineRunPipelineRunEventFragment on PipelineRunEvent {
        ...PipelineRunFilteredLogMessageFragment
        ...PipelineRunExecutionPlanPipelineRunEventFragment
      }

      ${PipelineRunExecutionPlan.fragments
        .PipelineRunExecutionPlanPipelineRunEventFragment}
      ${PipelineRunFilteredLogs.fragments.PipelineRunFilteredLogMessageFragment}
    `
  };

  state = {
    logsVH: 40,
    logsFilter: ""
  };

  render() {
    return (
      <PipelineRunWrapper>
        <PipelineRunExecutionPlan
          onSetLogFilter={logsFilter => this.setState({ logsFilter })}
          pipelineRun={this.props.pipelineRun}
        />
        <PanelDivider
          onMove={(vh: number) => this.setState({ logsVH: 100 - vh })}
          axis="vertical"
        />
        <LogsContainer style={{ height: `${this.state.logsVH}vh` }}>
          <PipelineRunFilteredLogs
            onSetFilter={logsFilter => this.setState({ logsFilter })}
            filter={this.state.logsFilter}
            nodes={this.props.pipelineRun.logs.nodes}
          />
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
`;

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  background: ${Colors.LIGHT_GRAY5};
`;
