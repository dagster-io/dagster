import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { ApolloConsumer } from "react-apollo";

import { PipelineRun, PipelineRunEmpty } from "./PipelineRun";
import { PanelDivider } from "../PanelDivider";
import PipelineSolidSelector from "./PipelineSolidSelector";
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
  currentRun: PipelineExecutionPipelineRunFragment | null;
  currentSession: IExecutionSession;
  onSaveSession: (session: string, changes: IExecutionSessionChanges) => void;
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
    const {pipeline, currentRun, currentSession } = this.props;

    if (!currentSession) {
      return <span />;
    }

    return (
      <PipelineExecutionWrapper>
        <Split width={this.state.editorVW}>
          <ApolloConsumer>
            {client => (
              <ConfigEditor
                configCode={currentSession.config}
                onConfigChange={this.onConfigChange}
                readOnly={false}
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
          {currentRun ? (
            <PipelineRun plan={currentRun.executionPlan} run={currentRun} />
          ) : (
            <PipelineRunEmpty />
          )}
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
  padding-top: 100px;
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
