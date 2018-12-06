import * as React from "react";

// Internal LocalStorage data format and mutation helpers

export interface IStorageData {
  sessions: { [name: string]: IExecutionSession };
  current: string;

  currentSession: () => IExecutionSession;
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
}

const DEFAULT_SESSION: IExecutionSession = {
  key: "default",
  name: "Default",
  config: "# This is config editor. Enjoy!"
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

export function applyNameToSession(
  data: IStorageData,
  key: string,
  newName: string
) {
  data.sessions[key].name = newName;
  return data;
}

export function applyConfigToSession(
  data: IStorageData,
  key: string,
  config: string
) {
  data.sessions[key].config = config;
  return data;
}

export function applyCreateSession(data: IStorageData) {
  const key = `s${Date.now()}`;
  data.sessions[key] = Object.assign({}, DEFAULT_SESSION, {
    key,
    name: "Untitled"
  });
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
    sessions: { default: Object.assign({}, DEFAULT_SESSION) },
    current: "default",

    currentSession() {
      return this.sessions[this.current];
    }
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
