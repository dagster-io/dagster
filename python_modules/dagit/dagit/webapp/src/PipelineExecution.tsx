import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";

import { ExecutionTab, ExecutionTabs } from "./ExecutionTabs";
import ConfigCodeEditorContainer from "./configeditor/ConfigCodeEditorContainer";
import { PipelineExecutionFragment } from "./types/PipelineExecutionFragment";
import Config from "./Config";
import {
  StorageProvider,
  applySelectSession,
  applyNameToSession,
  applyRemoveSession,
  applyConfigToSession,
  applyCreateSession
} from "./LocalStorage";

interface IPipelineExecutionProps {
  pipeline: PipelineExecutionFragment;
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
        contexts {
          config {
            ...ConfigFragment
          }
        }
      }
      ${Config.fragments.ConfigFragment}
    `
  };

  public render() {
    return (
      <Container>
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
      </Container>
    );
  }
}

const Container = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  top: 0;
  position: absolute;
  padding-top: 50px;
`;
