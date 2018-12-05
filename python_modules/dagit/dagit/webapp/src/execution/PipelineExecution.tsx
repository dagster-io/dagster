import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import * as yaml from "yaml";
import { Icon, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { ApolloClient } from "apollo-boost";

import { IExecutionSession } from "../LocalStorage";
import { PipelineRun, PipelineRunEmpty } from "./PipelineRun";
import { ExecutionTabs, ExecutionTab } from "./ExecutionTabs";

import {
  PipelineExecutionFragment,
  PipelineExecutionFragment_runs
} from "./types/PipelineExecutionFragment";
import ConfigCodeEditorContainer from "../configeditor/ConfigCodeEditorContainer";

interface IPipelineExecutionProps {
  pipeline: PipelineExecutionFragment;
  activeRun: PipelineExecutionFragment_runs | null;
  sessions: { [name: string]: IExecutionSession };
  currentSession: IExecutionSession;
  isExecuting: boolean;
  onSelectSession: (session: string) => void;
  onRenameSession: (session: string, title: string) => void;
  onSaveSession: (session: string, config: any) => void;
  onCreateSession: () => void;
  onRemoveSession: (session: string) => void;
  onExecute: (config: any) => void;
}

export default class PipelineExecution extends React.Component<
  IPipelineExecutionProps
> {
  static fragments = {
    PipelineExecutionFragment: gql`
      fragment PipelineExecutionFragment on Pipeline {
        name
        environmentType {
          name
        }
        runs {
          runId
          status
          logs {
            pageInfo {
              lastCursor
            }
          }
          ...PipelineRunFragment
        }
      }
      ${PipelineRun.fragments.PipelineRunFragment}
    `
  };

  render() {
    return (
      <>
        <ExecutionTabs>
          {Object.keys(this.props.sessions).map(key => (
            <ExecutionTab
              key={key}
              active={key === this.props.currentSession.key}
              title={this.props.sessions[key].name}
              onClick={() => this.props.onSelectSession(key)}
              onChange={title => this.props.onRenameSession(key, title)}
              onRemove={
                Object.keys(this.props.sessions).length > 1
                  ? () => this.props.onRemoveSession(key)
                  : undefined
              }
            />
          ))}
          <ExecutionTab
            title={"Add..."}
            onClick={() => this.props.onCreateSession()}
          />
        </ExecutionTabs>
        <PipelineExecutionWrapper>
          <Split>
            <ConfigCodeEditorContainer
              pipelineName={this.props.pipeline.name}
              environmentTypeName={this.props.pipeline.environmentType.name}
              configCode={this.props.currentSession.config}
              onConfigChange={config =>
                this.props.onSaveSession(this.props.currentSession.key, config)
              }
            />
          </Split>
          <Split>
            {this.props.activeRun ? (
              <PipelineRun pipelineRun={this.props.activeRun} />
            ) : (
              <PipelineRunEmpty />
            )}
          </Split>
          <IconWrapper
            role="button"
            disabled={this.props.isExecuting}
            onClick={async () => {
              if (!this.props.isExecuting) {
                let config = {};
                try {
                  config = yaml.parse(this.props.currentSession.config);
                } catch (err) {
                  alert(`Fix the errors in your config YAML and try again.`);
                  return;
                }
                this.props.onExecute(config);
              }
            }}
          >
            <Icon
              icon={this.props.isExecuting ? IconNames.REFRESH : IconNames.PLAY}
              iconSize={40}
            />
          </IconWrapper>
        </PipelineExecutionWrapper>
      </>
    );
  }
}

const PipelineExecutionWrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: row;
  width: 100%;

  height: 100vh;
  position: absolute;
  padding-top: 93px;
`;

const IconWrapper = styled.div<{ disabled: boolean }>`
  flex: 0 1 0;
  width: 60px;
  height: 60px;
  border-radius: 30px;
  background-color: ${Colors.GRAY5};
  position: absolute;
  left: calc(50% - 80px);
  top: 120px;
  justify-content: center;
  align-items: center;
  display: flex;
  cursor: ${({ disabled }) => (disabled ? "normal" : "pointer")};
  z-index: 2;

  &:hover {
    background-color: ${({ disabled }) =>
      disabled ? Colors.GRAY5 : Colors.GRAY4};
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
