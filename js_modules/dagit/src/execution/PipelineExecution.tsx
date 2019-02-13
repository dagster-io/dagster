import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { ApolloConsumer } from "react-apollo";

import { PipelineRun, PipelineRunEmpty } from "./PipelineRun";
import { ExecutionTabs, ExecutionTab } from "./ExecutionTabs";
import { PanelDivider } from "../PanelDivider";
import PipelineSolidSelector from "./PipelineSolidSelector";
import RunHistory from "./RunHistory";
import ExecutionStartButton from "./ExecutionStartButton";
import ConfigEditor from "../configeditor/ConfigEditor";
import {
  IExecutionSession,
  IExecutionSessionChanges,
  SESSION_CONFIG_PLACEHOLDER
} from "../LocalStorage";
import {
  CONFIG_EDITOR_PIPELINE_FRAGMENT,
  scaffoldConfig,
  checkConfig
} from "../configeditor/ConfigEditorUtils";

import { PipelineExecutionPipelineFragment } from "./types/PipelineExecutionPipelineFragment";
import { PipelineExecutionPipelineRunFragment } from "./types/PipelineExecutionPipelineRunFragment";

const CONFIRM_RESET_TO_SCAFFOLD = `Would you like to reset your config to a scaffold based on this subset of the pipeline?`;

interface IPipelineExecutionProps {
  pipeline: PipelineExecutionPipelineFragment;
  activeRun: PipelineExecutionPipelineRunFragment | null;
  sessions: { [name: string]: IExecutionSession };
  currentSession: IExecutionSession;
  onSelectSession: (session: string) => void;
  onSaveSession: (session: string, changes: IExecutionSessionChanges) => void;
  onCreateSession: () => void;
  onRemoveSession: (session: string) => void;
  onExecute: () => void;
}

interface IPipelineExecutionState {
  editorVW: number;
}

export default class PipelineExecution extends React.Component<
  IPipelineExecutionProps,
  IPipelineExecutionState
> {
  static fragments = {
    PipelineExecutionPipelineFragment: gql`
      fragment PipelineExecutionPipelineFragment on Pipeline {
        name
        environmentType {
          key
        }
        ...ConfigEditorPipelineFragment
      }
      ${CONFIG_EDITOR_PIPELINE_FRAGMENT}
    `,

    PipelineExecutionPipelineRunFragment: gql`
      fragment PipelineExecutionPipelineRunFragment on PipelineRun {
        runId
        status
        ...PipelineRunFragment
      }

      ${PipelineRun.fragments.PipelineRunFragment}
    `,

    PipelineExecutionPipelineRunEventFragment: gql`
      fragment PipelineExecutionPipelineRunEventFragment on PipelineRunEvent {
        ...PipelineRunPipelineRunEventFragment
      }
      ${PipelineRun.fragments.PipelineRunPipelineRunEventFragment}
    `
  };

  state = {
    editorVW: 50
  };

  componentDidMount() {
    this.ensureSessionStateValid();
  }

  componentDidUpdate() {
    this.ensureSessionStateValid();
  }

  ensureSessionStateValid() {
    const { onSaveSession, currentSession, pipeline } = this.props;

    // We have to initialize the sessions in local storage here because the app
    // needs to have the pieline (with the correct subset) in order to scaffold
    // the config YAML. In the future this could go in some sort of HOC I suppose.
    if (currentSession.config === SESSION_CONFIG_PLACEHOLDER) {
      onSaveSession(currentSession.key, { config: scaffoldConfig(pipeline) });
    }
  }

  onConfigChange = (config: any) => {
    this.props.onSaveSession(this.props.currentSession.key, { config });
  };

  onSolidSubsetChange = (solidSubset: string[] | null) => {
    const changes: IExecutionSessionChanges = { solidSubset };
    if (confirm(CONFIRM_RESET_TO_SCAFFOLD)) {
      changes.config = SESSION_CONFIG_PLACEHOLDER;
    }

    this.props.onSaveSession(this.props.currentSession.key, changes);
  };

  render() {
    const { sessions, pipeline, activeRun, currentSession } = this.props;

    if (!currentSession) {
      return <span />;
    }

    let activeRunExecuting = false;
    if (activeRun) {
      const start = activeRun.logs.nodes.find(
        l => l.__typename === "PipelineProcessStartEvent"
      );
      const end = activeRun.logs.nodes.find(
        l =>
          l.__typename === "PipelineSuccessEvent" ||
          l.__typename === "PipelineFailureEvent"
      );
      activeRunExecuting = start !== null && end == null;
    }

    return (
      <PipelineExecutionWrapper>
        <Split width={this.state.editorVW}>
          <ExecutionTabs>
            {Object.keys(sessions).map(key => (
              <ExecutionTab
                key={key}
                active={key === currentSession.key}
                title={sessions[key].name}
                onClick={() => this.props.onSelectSession(key)}
                onChange={name => this.props.onSaveSession(key, { name })}
                onRemove={
                  Object.keys(sessions).length > 1
                    ? () => this.props.onRemoveSession(key)
                    : undefined
                }
              />
            ))}
            <ExecutionTab
              title={"Add..."}
              onClick={() => {
                this.props.onCreateSession();
              }}
            />
          </ExecutionTabs>
          <ApolloConsumer>
            {client => (
              <ConfigEditor
                configCode={currentSession.config}
                onConfigChange={this.onConfigChange}
                pipeline={pipeline}
                checkConfig={json =>
                  checkConfig(client, json, {
                    name: pipeline.name,
                    solidSubset: currentSession.solidSubset
                  })
                }
              />
            )}
          </ApolloConsumer>
          <SessionSettingsFooter className="bp3-dark">
            <PipelineSolidSelector
              pipelineName={pipeline.name}
              value={currentSession.solidSubset || null}
              onChange={this.onSolidSubsetChange}
            />
          </SessionSettingsFooter>
        </Split>
        <PanelDivider
          axis="horizontal"
          onMove={(vw: number) => this.setState({ editorVW: vw })}
        />
        <Split>
          {activeRun ? (
            <PipelineRun pipelineRun={activeRun} />
          ) : (
            <PipelineRunEmpty />
          )}
          <ExecutionStartButton
            executing={activeRunExecuting}
            onClick={this.props.onExecute}
          />
        </Split>
        <PanelDivider axis="horizontal" onMove={() => {}} />
        <Split style={{flex: 0.5}}>
          <RunHistory activeRun={activeRun} pipelineName={pipeline.name} />
        </Split>
      </PipelineExecutionWrapper>
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
  padding-top: 50px;
`;

const SessionSettingsFooter = styled.div`
  color: white;
  display: flex;
  border-top: 1px solid ${Colors.DARK_GRAY5};
  background-color: ${Colors.DARK_GRAY2};
  align-items: center;
  padding: 8px;
}
`;

const Split = styled.div<{ width?: number }>`
  ${props => (props.width ? `width: ${props.width}vw` : `flex: 1`)};
  position: relative;
  flex-direction: column;
  display: flex;
`;
