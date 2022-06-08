import * as React from 'react';

import {getJSONForKey, useStateWithStorage} from '../hooks/useStateWithStorage';
import {LaunchpadSessionPartitionSetsFragment} from '../launchpad/types/LaunchpadSessionPartitionSetsFragment';
import {LaunchpadSessionPipelineFragment} from '../launchpad/types/LaunchpadSessionPipelineFragment';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';

import {AppContext} from './AppContext';

// Internal LocalStorage data format and mutation helpers

export interface IStorageData {
  sessions: {[name: string]: IExecutionSession};
  selectedExecutionType?: ExecutionType;
  current: string;
}

enum ExecutionType {
  START = 'start',
  LAUNCH = 'launch',
}

export interface PipelineRunTag {
  key: string;
  value: string;
}

export type SessionBase =
  | {presetName: string; tags: PipelineRunTag[] | null}
  | {partitionsSetName: string; partitionName: string | null; tags: PipelineRunTag[] | null};

export interface IExecutionSession {
  key: string;
  name: string;
  runConfigYaml: string;
  base: SessionBase | null;
  mode: string | null;
  needsRefresh: boolean;
  solidSelection: string[] | null;
  solidSelectionQuery: string | null;
  flattenGraphs: boolean;
  tags: PipelineRunTag[] | null;

  // this is set when you execute the session and freeze it
  runId?: string;
  configChangedSinceRun: boolean;
}

export type IExecutionSessionChanges = Partial<IExecutionSession>;

export function applySelectSession(data: IStorageData, key: string) {
  return {...data, current: key};
}

export function applyRemoveSession(data: IStorageData, key: string) {
  const next = {current: data.current, sessions: {...data.sessions}};
  const idx = Object.keys(next.sessions).indexOf(key);
  delete next.sessions[key];
  if (next.current === key) {
    const remaining = Object.keys(next.sessions);
    next.current = remaining[idx] || remaining[idx - 1] || remaining[0];
  }
  return next;
}

export function applyChangesToSession(
  data: IStorageData,
  key: string,
  changes: IExecutionSessionChanges,
) {
  const saved = data.sessions[key];
  if (changes.runConfigYaml && changes.runConfigYaml !== saved.runConfigYaml && saved.runId) {
    changes.configChangedSinceRun = true;
  }

  return {
    current: data.current,
    sessions: {...data.sessions, [key]: {...saved, ...changes}},
    selectedExecutionType: data.selectedExecutionType,
  };
}

export const createSingleSession = (initial: IExecutionSessionChanges = {}, key?: string) => {
  return {
    name: 'New Run',
    runConfigYaml: '',
    mode: null,
    base: null,
    needsRefresh: false,
    solidSelection: null,
    solidSelectionQuery: '*',
    flattenGraphs: false,
    tags: null,
    runId: undefined,
    ...initial,
    configChangedSinceRun: false,
    key: key || `s${Date.now()}`,
  };
};

export function applyCreateSession(
  data: IStorageData,
  initial: IExecutionSessionChanges = {},
): IStorageData {
  const key = `s${Date.now()}`;

  return {
    current: key,
    sessions: {
      ...data.sessions,
      [key]: createSingleSession(initial, key),
    },
    selectedExecutionType: data.selectedExecutionType,
  };
}

type StorageHook = [IStorageData, (data: IStorageData) => void];

const buildValidator = (initial: Partial<IExecutionSession> = {}) => (json: any): IStorageData => {
  let data: IStorageData = Object.assign({sessions: {}, current: ''}, json);

  if (Object.keys(data.sessions).length === 0) {
    data = applyCreateSession(data, initial);
  }

  if (!data.sessions[data.current]) {
    data.current = Object.keys(data.sessions)[0];
  }

  return data;
};

export const makeKey = (basePath: string, repoAddress: RepoAddress, pipelineOrJobName: string) =>
  `dagit.v2.${basePath}-${repoAddress.location}-${repoAddress.name}-${pipelineOrJobName}`;

export const makeOldKey = (repoAddress: RepoAddress, pipelineOrJobName: string) =>
  `dagit.v2.${repoAddress.name}.${pipelineOrJobName}`;

// todo DPE: Clean up the migration logic.
export function useExecutionSessionStorage(
  repoAddress: RepoAddress,
  pipelineOrJobName: string,
  initial: Partial<IExecutionSession> = {},
): StorageHook {
  const {basePath} = React.useContext(AppContext);

  const key = makeKey(basePath, repoAddress, pipelineOrJobName);
  const oldKey = makeOldKey(repoAddress, pipelineOrJobName);

  // Bind the validator function to the provided `initial` value. Convert to a JSON string
  // because we can't trust that the `initial` object is memoized.
  const initialAsJSON = JSON.stringify(initial);
  const validator = React.useMemo(
    () => buildValidator(JSON.parse(initialAsJSON) as Partial<IExecutionSession>),
    [initialAsJSON],
  );
  const [newState, setNewState] = useStateWithStorage(key, validator);

  // Read stored value for the old key. If a value is present, we will use it
  // for the new key, then remove the old key entirely.
  const oldValidator = React.useCallback((json: any) => json, []);
  const [oldState, setOldState] = useStateWithStorage(oldKey, oldValidator);

  React.useEffect(() => {
    if (oldState) {
      setNewState(oldState);

      // Delete data at old key.
      setOldState(undefined);
    }
  }, [oldState, setNewState, setOldState]);

  return [newState, setNewState];
}

const writeStorageDataForKey = (key: string, data: IStorageData) => {
  window.localStorage.setItem(key, JSON.stringify(data));
};

export type RepositoryToInvalidate = {
  locationName: string;
  name: string;
  pipelines: {name: string}[];
};

export const useInvalidateConfigsForRepo = () => {
  const [_, setVersion] = React.useState<number>(0);
  const {basePath} = React.useContext(AppContext);

  const onSave = React.useCallback(
    (repositories: RepositoryToInvalidate[]) => {
      repositories.forEach((repo) => {
        const {locationName, name, pipelines} = repo;
        const pipelineNames = pipelines.map((pipeline) => pipeline.name);
        const repoAddress = buildRepoAddress(name, locationName);

        pipelineNames.forEach((pipelineName) => {
          const key = makeKey(basePath, repoAddress, pipelineName);
          const data: IStorageData | undefined = getJSONForKey(key);
          if (data) {
            const withBase = Object.keys(data.sessions).filter(
              (sessionKey) => data.sessions[sessionKey].base !== null,
            );
            if (withBase.length) {
              const withUpdates = withBase.reduce(
                (accum, sessionKey) =>
                  applyChangesToSession(accum, sessionKey, {needsRefresh: true}),
                data,
              );
              writeStorageDataForKey(key, withUpdates);
            }
          }
        });
      });

      setVersion((current) => current + 1);
    },
    [basePath],
  );

  return onSave;
};

export const useInitialDataForMode = (
  pipeline: LaunchpadSessionPipelineFragment,
  partitionSets: LaunchpadSessionPartitionSetsFragment,
) => {
  const {isJob, presets} = pipeline;
  const partitionSetsForMode = partitionSets.results;

  return React.useMemo(() => {
    const presetsForMode = isJob ? (presets.length ? [presets[0]] : []) : presets;

    if (presetsForMode.length === 1 && partitionSetsForMode.length === 0) {
      return {
        base: {presetName: presetsForMode[0].name, tags: null},
        runConfigYaml: presetsForMode[0].runConfigYaml,
      };
    }

    if (!presetsForMode.length && partitionSetsForMode.length === 1) {
      return {
        base: {partitionsSetName: partitionSetsForMode[0].name, partitionName: null, tags: null},
      };
    }

    return {};
  }, [isJob, partitionSetsForMode, presets]);
};
