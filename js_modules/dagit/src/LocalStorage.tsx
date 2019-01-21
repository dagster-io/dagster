import * as React from "react";

// Internal LocalStorage data format and mutation helpers

export interface IStorageData {
  sessions: { [name: string]: IExecutionSession };
  current: string;
}

export interface IExecutionSessionPlan {
  steps: Array<{
    name: string;
    tag: string;
    solid: {
      name: string;
    };
  }>;
}

export interface IExecutionSessionRun {
  executionParams: {
    pipelineName: string;
    config: object;
  };
  executionPlan: IExecutionSessionPlan;
  runId: string;
}

export interface IExecutionSession {
  key: string;
  name: string;
  config: string;
  solidSubset: string[] | null;
}

export interface IExecutionSessionChanges {
  name?: string;
  config?: string;
  solidSubset?: string[] | null;
}

// When we create a new session, we insert a placeholder config that is swapped
// with a scaffold when the pipeline with the desired solidSubset has loaded
// and we're able to assemble the YAML.
export const SESSION_CONFIG_PLACEHOLDER = "SCAFFOLD-PLACEHOLDER";

const DEFAULT_SESSION: IExecutionSession = {
  key: "default",
  name: "Untitled",
  config: SESSION_CONFIG_PLACEHOLDER,
  solidSubset: null
};

export function applySelectSession(data: IStorageData, key: string) {
  data.current = key;
  return data;
}

export function applyRemoveSession(data: IStorageData, key: string) {
  const idx = Object.keys(data.sessions).indexOf(key);
  delete data.sessions[key];
  if (data.current === key) {
    const remainingKeys = Object.keys(data.sessions);
    data.current = remainingKeys[idx] || remainingKeys[0];
  }
  return data;
}

export function applyChangesToSession(
  data: IStorageData,
  key: string,
  changes: IExecutionSessionChanges
) {
  Object.assign(data.sessions[key], changes);
  return data;
}

export function applyCreateSession(data: IStorageData) {
  const key = `s${Date.now()}`;
  data.sessions[key] = Object.assign({}, DEFAULT_SESSION, { key });
  data.current = key;
  return data;
}

// StorageProvider component that vends `IStorageData` via a render prop

interface IStorageProviderRenderProps {
  data: IStorageData;
  onSave: (data: IStorageData) => void;
}

export interface IStorageProviderProps {
  namespace: string;
  children: (props: IStorageProviderRenderProps) => React.ReactChild;
}

interface IStorageProviderState extends IStorageData {}

export class StorageProvider extends React.Component<
  IStorageProviderProps,
  IStorageProviderState
> {
  public state: IStorageProviderState = {
    sessions: {},
    current: ""
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

    // Ensure the data is consistent and that there is always a "current" session
    // if loading has
    if (Object.keys(this.state.sessions).length === 0) {
      this.state = applyCreateSession(this.state);
    }
    if (!this.state.sessions[this.state.current]) {
      this.state.current = Object.keys(this.state.sessions)[0];
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
