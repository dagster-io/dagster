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
  environmentConfigYaml: string;
  mode: string | null;
  solidSubset: string[] | null;

  // this is set when you execute the session and freeze it
  runId?: string;
  configChangedSinceRun: boolean;
}

export type IExecutionSessionChanges = Partial<IExecutionSession>;

const DEFAULT_SESSION: IExecutionSession = {
  key: "default",
  name: "Workspace",
  environmentConfigYaml: "",
  mode: null,
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
  if (
    changes.environmentConfigYaml &&
    changes.environmentConfigYaml !== saved.environmentConfigYaml &&
    saved.runId
  ) {
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

export type StorageHook = [
  IStorageData,
  React.Dispatch<React.SetStateAction<IStorageData>>
];

function getStorageDataForNamespace(namespace: string) {
  let data: IStorageData = {
    sessions: {},
    current: ""
  };
  try {
    const jsonString = window.localStorage.getItem(`dagit.${namespace}`);
    if (jsonString) {
      data = Object.assign(data, JSON.parse(jsonString));
    }
  } catch (err) {
    // noop
  }
  if (Object.keys(data.sessions).length === 0) {
    data = applyCreateSession(data);
  }
  if (!data.sessions[data.current]) {
    data.current = Object.keys(data.sessions)[0];
  }
  return data;
}

export function useStorage({ namespace }: { namespace: string }): StorageHook {
  const [data, setData] = React.useState<IStorageData>(() =>
    getStorageDataForNamespace(namespace)
  );

  React.useEffect(() => {
    // When the namespace changes, re-initialize the data by reading from LocalStorage
    // and running a few consistency checks to ensure a valid state.
    setData(getStorageDataForNamespace(namespace));
  }, [namespace]);

  const onSave = (newData: IStorageData) => {
    setData(newData);
    window.localStorage.setItem(`dagit.${namespace}`, JSON.stringify(newData));
  };

  return [data, onSave];
}
