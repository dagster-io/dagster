import * as React from 'react'

// Internal LocalStorage data format and mutation helpers

export interface IStorageData {
  sessions: { [name: string]: IExecutionSession };
  current: string;
}

export interface IExecutionSession {
  name: string;
  config: string;
}

const DEFAULT_SESSION: IExecutionSession = {
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

export function applyNameToSession(data: IStorageData, newName: string) {
  data.sessions[data.current].name = newName;
  return data;
}

export function applyConfigToSession(data: IStorageData, config: string) {
  data.sessions[data.current].config = config;
  return data;
}

export function applyCreateSession(data: IStorageData) {
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