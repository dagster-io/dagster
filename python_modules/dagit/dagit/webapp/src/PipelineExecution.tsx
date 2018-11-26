import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import ConfigCodeEditorContainer from "./configeditor/ConfigCodeEditorContainer";
import { PipelineExecutionFragment } from "./types/PipelineExecutionFragment";
import Config from "./Config";

interface IPipelineExecutionProps {
  pipeline: PipelineExecutionFragment;
}

interface IPipelineExecutionState {
  configCode: string;
}

export default class PipelineExecution extends React.Component<
  IPipelineExecutionProps,
  IPipelineExecutionState
> {
  static fragments = {
    PipelineExecutionFragment: gql`
      fragment PipelineExecutionFragment on Pipeline {
        name
        environmentType {
          name
        }
        contexts {
          config {
            ...ConfigFragment
          }
        }
      }
      ${Config.fragments.ConfigFragment}
    `
  };

  constructor(props: IPipelineExecutionProps) {
    super(props);
    const configKey = getConfigStorageKey(props.pipeline);
    let configCode = localStorage.getItem(configKey);
    if (!configCode || typeof configCode !== "string") {
      configCode = "# This is config editor. Enjoy!";
    }
    this.state = { configCode };
  }

  handleConfigChange = (newValue: string) => {
    const configKey = getConfigStorageKey(this.props.pipeline);
    localStorage.setItem(configKey, newValue);
    this.setState({ configCode: newValue });
  };

  public render() {
    return (
      <Container>
        <ConfigCodeEditorContainer
          pipelineName={this.props.pipeline.name}
          environmentTypeName={this.props.pipeline.environmentType.name}
          configCode={this.state.configCode}
          onConfigChange={this.handleConfigChange}
        />
      </Container>
    );
  }
}

function getConfigStorageKey(pipeline: PipelineExecutionFragment) {
  return `dagit.pipelineConfigStorage.${pipeline.name}`;
}

const Container = styled.div`
  flex: 1 1;
  display: flex;
  width: 100%;
  height: 100vh;
  top: 0;
  position: absolute;
  padding-top: 50px;
`;
