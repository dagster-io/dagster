import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";

import { ExecutionTab, ExecutionTabs } from "./ExecutionTabs";
import ConfigCodeEditorContainer from "./configeditor/ConfigCodeEditorContainer";
import { PipelineExecutionFragment } from "./types/PipelineExecutionFragment";
import Config from "./Config";

// Internal LocalStorage data format and mutation helpers

interface IStorageData {
  sessions: { [name: string]: IExecutionSession };
  current: string;
}

interface IExecutionSession {
  name: string;
  config: string;
}

const DEFAULT_SESSION: IExecutionSession = {
  name: "Default",
  config: "# This is config editor. Enjoy!"
};

function applySelectSession(data: IStorageData, key: string) {
  data.current = key;
  return data;
}

function applyRemoveSession(data: IStorageData, key: string) {
  const idx = Object.keys(data.sessions).indexOf(key);
  delete data.sessions[key];
  if (data.current === key) {
    const remainingKeys = Object.keys(data.sessions);
    data.current = remainingKeys[idx] || remainingKeys[0];
  }
  return data;
}

function applyNameToSession(data: IStorageData, newName: string) {
  data.sessions[data.current].name = newName;
  return data;
}

function applyConfigToSession(data: IStorageData, config: string) {
  data.sessions[data.current].config = config;
  return data;
}

function applyCreateSession(data: IStorageData) {
  const key = `s${Date.now()}`;
  data.sessions[key] = Object.assign({}, DEFAULT_SESSION, { name: "Untitled" });
  data.current = key;
  return data;
}

// StorageProvider component that vends `IStorageData` via a render prop

interface IStorageProviderRenderProps {
  data: IStorageData;
  onSave: (data: IStorageData) => void;
}

interface IStorageProviderProps {
  namespace: string;
  children: (props: IStorageProviderRenderProps) => React.ReactChild;
}

interface IStorageProviderState extends IStorageData {}

interface IPipelineExecutionProps {
  pipeline: PipelineExecutionFragment;
}

export class StorageProvider extends React.Component<
  IStorageProviderProps,
  IStorageProviderState
> {
  public state: IStorageProviderState = {
    sessions: { default: Object.assign({}, DEFAULT_SESSION) },
    current: "default"
  };

  constructor(props: IStorageProviderProps) {
    super(props);

    try {
      const jsonString = window.localStorage.getItem(
        `dagit.${props.namespace}`
      );
      if (jsonString) {
        this.state = Object.assign(this.state, JSON.parse(jsonString));
      }
    } catch (err) {
      // noop
    }
  }

  componentDidUpdate() {
    window.localStorage.setItem(
      `dagit.${this.props.namespace}`,
      JSON.stringify(this.state)
    );
  }

  render() {
    return this.props.children({
      data: this.state,
      onSave: data => this.setState(data)
    });
  }
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
