import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Icon } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { PipelineRunLogMessageFragment } from "./types/PipelineRunLogMessageFragment";

interface IPipelineRunLogMessageProps {
  log: PipelineRunLogMessageFragment;
}

export default class PipelineRunLogMessage extends React.Component<
  IPipelineRunLogMessageProps
> {
  static fragments = {
    PipelineRunLogMessageFragment: gql`
      fragment PipelineRunLogMessageFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
        }
      }
    `
  };

  render() {
    if (this.props.log.__typename === "PipelineStartEvent") {
      return (
        <LogMessage>
          <IconWrapper>
            <Icon icon={IconNames.PLAY} />
          </IconWrapper>

          {this.props.log.message}
        </LogMessage>
      );
    } else if (this.props.log.__typename === "PipelineSuccessEvent") {
      return (
        <LogMessage>
          <IconWrapper>
            <Icon icon={IconNames.TICK_CIRCLE} />
          </IconWrapper>

          {this.props.log.message}
        </LogMessage>
      );
    } else if (this.props.log.__typename === "PipelineFailureEvent") {
      return (
        <LogMessage>
          <IconWrapper>
            <Icon icon={IconNames.ERROR} />
          </IconWrapper>
          {this.props.log.message}
        </LogMessage>
      );
    } else {
      return <LogMessage>{this.props.log.message}</LogMessage>;
    }
  }
}

const LogMessage = styled.div`
  color: ${Colors.WHITE};
  padding: 5px;
  border-bottom: 1px solid ${Colors.GRAY1};
`;

const IconWrapper = styled.span`
  margin-right: 5px;
`;
