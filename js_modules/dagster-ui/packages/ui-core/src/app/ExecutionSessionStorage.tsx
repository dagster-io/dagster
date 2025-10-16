import memoize from 'lodash/memoize';
import * as React from 'react';

import {AppContext} from './AppContext';
import {AssetCheck, AssetKeyInput} from '../graphql/types';
import {useSetStateUpdateCallback} from '../hooks/useSetStateUpdateCallback';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {
  LaunchpadSessionPartitionSetsFragment,
  LaunchpadSessionPipelineFragment,
} from '../launchpad/types/LaunchpadAllowedRoot.types';
import {getJSONForKey} from '../util/getJSONForKey';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';

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
  | {
      type: 'preset';
      presetName: string;
      tags: PipelineRunTag[] | null;
    }
  | {
      type: 'asset-job-partition';
      partitionName: string | null;
      tags: PipelineRunTag[] | null;
    }
  | {
      type: 'op-job-partition-set';
      partitionsSetName: string;
      partitionName: string | null;
      tags: PipelineRunTag[] | null;
    };

export interface IExecutionSession {
  key: string;
  name: string;
  runConfigYaml: string;
  base: SessionBase | null;
  mode: string | null;
  needsRefresh: boolean;
  assetSelection: {assetKey: AssetKeyInput; opNames?: string[]}[] | null;
  // Nullable for backwards compatibility
  assetChecksAvailable?: Pick<AssetCheck, 'name' | 'canExecuteIndividually' | 'assetKey'>[];
  includeSeparatelyExecutableChecks: boolean;
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    next.current = remaining[idx] || remaining[idx - 1] || remaining[0]!;
  }
  return next;
}

export function applyChangesToSession(
  data: IStorageData,
  key: string,
  changes: IExecutionSessionChanges,
) {
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const saved = data.sessions[key]!;
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
    assetSelection: null,
    assetChecksAvailable: [],
    includeSeparatelyExecutableChecks: true,
    solidSelection: null,
    solidSelectionQuery: '*',
    flattenGraphs: false,
    tags: null,
    runId: undefined,

    // This isn't really safe, since it could spread in `undefined` values that
    // override the default values above.
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

type StorageHook = [IStorageData, (data: React.SetStateAction<IStorageData>) => void];

const buildValidator =
  (initial: Partial<IExecutionSession> = {}) =>
  (json: any): IStorageData => {
    let data: IStorageData = Object.assign({sessions: {}, current: ''}, json);

    if (Object.keys(data.sessions).length === 0) {
      data = applyCreateSession(data, initial);
    }

    if (!data.sessions[data.current]) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      data.current = Object.keys(data.sessions)[0]!;
    }

    return data;
  };

const makeKey = (basePath: string, repoAddress: RepoAddress, pipelineOrJobName: string) =>
  `dagster.v2.${basePath}-${repoAddress.location}-${repoAddress.name}-${pipelineOrJobName}`;

export function useExecutionSessionStorage(
  repoAddress: RepoAddress,
  pipelineOrJobName: string,
  initial: Partial<IExecutionSession> = {},
): StorageHook {
  const {basePath} = React.useContext(AppContext);

  const key = makeKey(basePath, repoAddress, pipelineOrJobName);

  // Bind the validator function to the provided `initial` value. Convert to a JSON string
  // because we can't trust that the `initial` object is memoized.
  const initialAsJSON = JSON.stringify(initial);
  const validator = React.useMemo(
    () => buildValidator(JSON.parse(initialAsJSON) as Partial<IExecutionSession>),
    [initialAsJSON],
  );

  const [state, setState] = useStateWithStorage(key, validator);
  const wrappedSetState = useSetStateUpdateCallback(
    state,
    writeLaunchpadSessionToStorage(setState),
  );

  return [state, wrappedSetState];
}

const writeStorageDataForKey = (key: string, data: IStorageData) => {
  window.localStorage.setItem(key, JSON.stringify(data));
};

type RepositoryToInvalidate = {
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
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              (sessionKey) => data.sessions[sessionKey]!.base !== null,
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
  rootDefaultYaml: string | undefined,
  shouldPopulateWithDefaults: boolean,
): {base?: SessionBase; runConfigYaml?: string} => {
  const {isJob, isAssetJob, presets} = pipeline;
  const partitionSetsForMode = partitionSets.results;

  return React.useMemo(() => {
    const presetsForMode = isJob ? (presets.length ? [presets[0]] : []) : presets;

    // I believe that partition sets in asset jobs do not provide config (at least right now),
    // so even in the presence of a partition set we want to use config from the
    // `default` preset
    if (presetsForMode.length === 1 && (isAssetJob || partitionSetsForMode.length === 0)) {
      return {
        base: {
          type: 'preset',
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          presetName: presetsForMode[0]!.name,
          tags: null,
        },
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        runConfigYaml: presetsForMode[0]!.runConfigYaml,
      };
    }

    if (!presetsForMode.length && partitionSetsForMode.length === 1) {
      return {
        base: {
          type: 'op-job-partition-set',
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          partitionsSetName: partitionSetsForMode[0]!.name,
          partitionName: null,
          tags: null,
        },
        runConfigYaml: rootDefaultYaml,
      };
    }

    return shouldPopulateWithDefaults ? {runConfigYaml: rootDefaultYaml} : {};
  }, [
    isAssetJob,
    isJob,
    partitionSetsForMode,
    presets,
    rootDefaultYaml,
    shouldPopulateWithDefaults,
  ]);
};

export const allStoredSessions = () => {
  const storedSessions: [sessionID: string, jobKey: string][] = [];
  for (let ii = 0; ii < window.localStorage.length; ii++) {
    const key = window.localStorage.key(ii);
    if (key) {
      const value = window.localStorage.getItem(key);
      if (value) {
        let parsed;

        // If it's not a parseable object, it's not a launchpad session.
        try {
          parsed = JSON.parse(value);
        } catch {
          continue;
        }

        if (
          parsed &&
          typeof parsed === 'object' &&
          parsed.hasOwnProperty('current') &&
          parsed.hasOwnProperty('sessions')
        ) {
          const sessionIDs = Object.keys(parsed.sessions);
          storedSessions.push(
            ...sessionIDs.map((sessionID) => [key, sessionID] as [string, string]),
          );
        }
      }
    }
  }

  // Order the list of sessions by timestamp.
  storedSessions.sort(([_aKey, sessionA], [_bKey, sessionB]) => {
    const timeA = parseInt(sessionA.slice(1), 10);
    const timeB = parseInt(sessionB.slice(1), 10);
    return timeA - timeB;
  });

  return storedSessions;
};

export const removeSession = (jobKey: string, sessionID: string) => {
  const item = window.localStorage.getItem(jobKey);
  if (item) {
    const data = JSON.parse(item);
    const updated = applyRemoveSession(data, sessionID);
    window.localStorage.setItem(jobKey, JSON.stringify(updated));
  }
};

export const MAX_SESSION_WRITE_ATTEMPTS = 10;

/**
 * Try to write this launchpad session to storage. If a quota error occurs because the
 * user has too much data already in localStorage, clear out old sessions until the
 * write is successful or we run out of retries.
 */
export const writeLaunchpadSessionToStorage =
  (setState: React.Dispatch<React.SetStateAction<IStorageData>>) => (data: IStorageData) => {
    const tryWrite = (data: IStorageData) => {
      try {
        setState(data);
        return true;
      } catch {
        // The data could not be written to localStorage. This is probably due to
        // a QuotaExceededError, but since different browsers use slightly different
        // objects for this, we don't try to get clever detecting it.
        return false;
      }
    };

    const getInitiallyStoredSessions = memoize(() => allStoredSessions());

    // Track the number of attempts at writing this session to localStorage so that
    // we eventually give up and don't loop endlessly.
    let attempts = 1;

    // Attempt to write the session to storage. If an error occurs, delete the oldest
    // session and try again.
    while (!tryWrite(data) && attempts < MAX_SESSION_WRITE_ATTEMPTS) {
      attempts++;

      // Remove the oldest session and try again.
      const toRemove = getInitiallyStoredSessions().shift();
      if (toRemove) {
        const [jobKey, sessionID] = toRemove;
        removeSession(jobKey, sessionID);
      }
    }
  };
