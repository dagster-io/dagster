import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Icon, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";

import { ExecutionTab, ExecutionTabs } from "./ExecutionTabs";
import ConfigCodeEditorContainer from "./configeditor/ConfigCodeEditorContainer";
import Config from "./Config";
import PipelineRunsLogs from "./PipelineRunsLogs";
import {
  StorageProvider,
  applySelectSession,
  applyNameToSession,
  applyRemoveSession,
  applyConfigToSession,
  applyCreateSession
} from "./LocalStorage";
import { PipelineExecutionFragment } from "./types/PipelineExecutionFragment";

interface IPipelineExecutionProps {
  pipeline: PipelineExecutionFragment;
}

interface IPipelineExecutionState {
  selectedRun: string | null;
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
        runs {
          ...PipelineRunsLogsFragment
        }
      }
      ${Config.fragments.ConfigFragment}
      ${PipelineRunsLogs.fragments.PipelineRunsLogsFragment}
    `
  };

  state = {
    selectedRun: this.props.pipeline.runs.length
      ? this.props.pipeline.runs[0].runId
      : null
  };

  static getDerivedStateFromProps(
    props: IPipelineExecutionProps,
    state: IPipelineExecutionState
  ) {
    if (state.selectedRun === null && props.pipeline.runs.length > 0) {
      return {
        selectedRun: props.pipeline.runs[0].runId
      };
    }
    return null;
  }

  handleSelectRun = (newRun: string) => {
    this.setState({
      selectedRun: newRun
    });
  };

  renderConfigEditor() {
    return (
      <StorageProvider namespace={this.props.pipeline.name}>
        {({ data, onSave }) => (
          <>
            <ExecutionTabs>
              {Object.keys(data.sessions).map(key => (
                <ExecutionTab
                  key={key}
                  active={key === data.current}
                  title={data.sessions[key].name}
                  onClick={() => onSave(applySelectSession(data, key))}
                  onChange={title => onSave(applyNameToSession(data, title))}
                  onRemove={
                    Object.keys(data.sessions).length > 1
                      ? () => onSave(applyRemoveSession(data, key))
                      : undefined
                  }
                />
              ))}
              <ExecutionTab
                title={"Add..."}
                onClick={() => onSave(applyCreateSession(data))}
              />
            </ExecutionTabs>
            <ConfigCodeEditorContainer
              pipelineName={this.props.pipeline.name}
              environmentTypeName={this.props.pipeline.environmentType.name}
              configCode={data.sessions[data.current].config}
              onConfigChange={config =>
                onSave(applyConfigToSession(data, config))
              }
            />
          </>
        )}
      </StorageProvider>
    );
  }

  renderPipelineRunss() {
    if (this.state.selectedRun) {
      return (
        <PipelineRunsLogs
          runs={this.props.pipeline.runs}
          selectedRun={this.state.selectedRun}
          onSelectRun={this.handleSelectRun}
        />
      );
    } else {
      return <EmptyRunLogs />;
    }
  }

  public render() {
    return (
      <Container>
        <Split>{this.renderConfigEditor()}</Split>
        <Split>{this.renderPipelineRunss()}</Split>
        <IconWrapper role="button">
          <Icon icon={IconNames.PLAY} iconSize={40} />
        </IconWrapper>
      </Container>
    );
  }
}

const Container = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100vh;
  top: 0;
  position: absolute;
  padding-top: 50px;
`;

const IconWrapper = styled.div`
  flex: 0 1 0;
  width: 60px;
  height: 60px;
  border-radius: 30px;
  background-color: ${Colors.GRAY5};
  position: absolute;
  left: calc(50% - 30px);
  top: 120px;
  justify-content: center;
  align-items: center;
  display: flex;
  padding-left: 6px;
  cursor: pointer;

  &:hover {
    background-color: ${Colors.GRAY4};
  }

  &:active {
    background-color: ${Colors.GRAY3};
  }
`;

const Split = styled.div`
  flex: 1 1;
  flex-direction: column;
  display: flex;
`;

const EmptyRunLogs = styled.div`
  flex: 1 1;
  flex-direction: column;
  display: flex;
  background: ${Colors.BLACK};
`;
