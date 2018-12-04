import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import PipelineRunLogMessage from "./PipelineRunLogMessage";
import { PipelineRunLogsFragment } from "./types/PipelineRunLogsFragment";

interface IPipelineRunLogsProps {
  logs: Array<PipelineRunLogsFragment>;
}

export default class PipelineRunLogs extends React.Component<
  IPipelineRunLogsProps
> {
  static fragments = {
    PipelineRunLogsFragment: gql`
      fragment PipelineRunLogsFragment on PipelineRunEvent {
        ...PipelineRunLogMessageFragment
      }

      ${PipelineRunLogMessage.fragments.PipelineRunLogMessageFragment}
    `
  };

  renderLogs() {
    return this.props.logs.map((log, i) => {
      return <PipelineRunLogMessage key={i} log={log} />;
    });
  }

  render() {
    return (
      <PipelineRunLogsContainer>{this.renderLogs()}</PipelineRunLogsContainer>
    );
  }
}

const PipelineRunLogsContainer = styled.div`
  padding-left: 35px;
  padding-top: 5px;
  padding-bottom: 5px;
  display: flex;
  flex: 1 1;
  flex-direction: column;
`;
