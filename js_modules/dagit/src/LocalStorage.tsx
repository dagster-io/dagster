import * as React from "react";

// Internal LocalStorage data format and mutation helpers

export interface IStorageData {
  sessions: { [name: string]: IExecutionSession };
  current: string;
}

export interface IExecutionSessionPlan {
  steps: Array<{
    name: string;
    kind: string;
    solid: {
      name: string;
    };
  }>;
}

export interface IExecutionSession {
  key: string;
  name: string;
  config: string;
  solidSubset: string[] | null;

  // this is set when you execute the session and freeze it
  runId?: string;
  configChangedSinceRun: boolean;
}

export type IExecutionSessionChanges = Partial<IExecutionSession>;

const DEFAULT_SESSION: IExecutionSession = {
  key: "default",
  name: "Workspace",
  config: "",
  solidSubset: null,
  runId: undefined,
  configChangedSinceRun: false
};

export function applySelectSession(data: IStorageData, key: string) {
  return { ...data, current: key };
}

export function applyRemoveSession(data: IStorageData, key: string) {
  const next = { current: data.current, sessions: { ...data.sessions } };
  const idx = Object.keys(next.sessions).indexOf(key);
  delete next.sessions[key];
  if (next.current === key) {
    const remainingKeys = Object.keys(next.sessions);
    next.current = remainingKeys[idx] || remainingKeys[0];
  }
  return next;
}

export function applyChangesToSession(
  data: IStorageData,
  key: string,
  changes: IExecutionSessionChanges
) {
  const saved = data.sessions[key];
  if (changes.config && changes.config !== saved.config && saved.runId) {
    changes.configChangedSinceRun = true;
  }

  return {
    current: data.current,
    sessions: { ...data.sessions, [key]: { ...saved, ...changes } }
  };
}

export function applyCreateSession(
  data: IStorageData,
  initial: IExecutionSessionChanges = {}
) {
  const key = `s${Date.now()}`;

  return {
    current: key,
    sessions: {
      ...data.sessions,
      [key]: Object.assign({}, DEFAULT_SESSION, initial, {
        configChangedSinceRun: false,
        key
      })
    }
  };
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
