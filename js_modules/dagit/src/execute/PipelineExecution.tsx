import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { ApolloConsumer } from "react-apollo";

import { RunPreview } from "./RunPreview";
import { PanelDivider } from "../PanelDivider";
import SolidSelector from "./SolidSelector";
import ConfigEditor from "../configeditor/ConfigEditor";
import {
  PreviewConfigQuery,
  PreviewConfigQueryVariables
} from "./types/PreviewConfigQuery";

import {
  IExecutionSession,
  IExecutionSessionChanges,
  SESSION_CONFIG_PLACEHOLDER
} from "../LocalStorage";
import {
  CONFIG_EDITOR_PIPELINE_FRAGMENT,
  CONFIG_EDITOR_VALIDATION_FRAGMENT,
  scaffoldConfig,
  responseToValidationResult
} from "../configeditor/ConfigEditorUtils";

import { PipelineExecutionPipelineFragment } from "./types/PipelineExecutionPipelineFragment";

const CONFIRM_RESET_TO_SCAFFOLD = `Would you like to reset your config to a scaffold based on this subset of the pipeline?`;

interface IPipelineExecutionProps {
  pipeline?: PipelineExecutionPipelineFragment;
  currentSession: IExecutionSession;
  onSaveSession: (session: string, changes: IExecutionSessionChanges) => void;
}

interface IPipelineExecutionState {
  editorVW: number;
  preview: PreviewConfigQuery | null;
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
    `
  };

  state: IPipelineExecutionState = {
    editorVW: 75,
    preview: null
  };

  mounted = false;

  componentDidMount() {
    this.mounted = true;
    this.ensureSessionStateValid();
  }

  componentDidUpdate() {
    this.ensureSessionStateValid();
  }

  componentWillUnmount() {
    this.mounted = false;
  }

  ensureSessionStateValid() {
    const { onSaveSession, currentSession, pipeline } = this.props;
    if (!pipeline) return;

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
    const { pipeline, currentSession } = this.props;
    const { preview } = this.state;

    if (!currentSession) {
      return <span />;
    }

    return (
      <PipelineExecutionWrapper>
        <Split width={this.state.editorVW} style={{ flexShrink: 0 }}>
          <ApolloConsumer>
            {client => (
              <ConfigEditor
                readOnly={false}
                pipeline={pipeline}
                configCode={currentSession.config}
                onConfigChange={this.onConfigChange}
                checkConfig={async config => {
                  if (!pipeline) return { isValid: true };

                  const { data } = await client.query<
                    PreviewConfigQuery,
                    PreviewConfigQueryVariables
                  >({
                    fetchPolicy: "no-cache",
                    query: PREVIEW_CONFIG_QUERY,
                    variables: {
                      config,
                      pipeline: {
                        name: pipeline.name,
                        solidSubset: currentSession.solidSubset
                      }
                    }
                  });

                  this.setState({ preview: data });

                  return responseToValidationResult(
                    config,
                    data.isPipelineConfigValid
                  );
                }}
              />
            )}
          </ApolloConsumer>
          <SessionSettingsFooter className="bp3-dark">
            {!pipeline ? (
              <span />
            ) : (
              <SolidSelector
                pipelineName={pipeline.name}
                value={currentSession.solidSubset || null}
                onChange={this.onSolidSubsetChange}
              />
            )}
          </SessionSettingsFooter>
        </Split>
        <PanelDivider
          axis="horizontal"
          onMove={(vw: number) => this.setState({ editorVW: vw })}
        />
        <Split>
          {preview ? (
            <RunPreview
              plan={preview.executionPlan}
              validation={preview.isPipelineConfigValid}
            />
          ) : (
            <RunPreview />
          )}
        </Split>
      </PipelineExecutionWrapper>
    );
  }
}

const PREVIEW_CONFIG_QUERY = gql`
  query PreviewConfigQuery(
    $pipeline: ExecutionSelector!
    $config: PipelineConfig!
  ) {
    isPipelineConfigValid(pipeline: $pipeline, config: $config) {
      ...ConfigEditorValidationFragment
      ...RunPreviewConfigValidationFragment
    }
    executionPlan(pipeline: $pipeline, config: $config) {
      ...RunPreviewExecutionPlanResultFragment
    }
  }
  ${RunPreview.fragments.RunPreviewConfigValidationFragment}
  ${RunPreview.fragments.RunPreviewExecutionPlanResultFragment}
  ${CONFIG_EDITOR_VALIDATION_FRAGMENT}
`;

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
  height: 47px;
  padding: 8px;
}
`;

const Split = styled.div<{ width?: number }>`
  ${props => (props.width ? `width: ${props.width}vw` : `flex: 1`)};
  position: relative;
  flex-direction: column;
  display: flex;
`;
