import React, {useContext} from 'react';

import {CODE_LOCATION_FILTER_KEY, HIDDEN_REPO_KEYS, WorkspaceContext} from './WorkspaceContext';
import {
  PartialWorkspaceLocationNodeFragment,
  WorkspaceLocationAssetsEntryFragment,
  WorkspaceLocationFragment,
  WorkspaceLocationNodeFragment,
  WorkspaceRepositoryAssetsFragment,
  WorkspaceRepositoryFragment,
} from './types/WorkspaceQueries.types';
import {AppContext} from '../../app/AppContext';
import {PipelineSelector} from '../../graphql/types';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {buildRepoAddress} from '../buildRepoAddress';
import {findRepoContainingPipeline} from '../findRepoContainingPipeline';
import {RepoAddress} from '../types';

type Repository = WorkspaceRepositoryFragment;
type RepositoryLocation = WorkspaceLocationFragment;
export interface DagsterRepoOption {
  repositoryLocation: RepositoryLocation;
  repository: Repository;
}

/**
 * useVisibleRepos returns `{reposForKeys, toggleVisible, setVisible, setHidden}` and internally
 * mirrors the current selection into localStorage so that the default selection in new browser
 * windows is the repo currently active in your session.
 */
export const validateHiddenKeys = (parsed: unknown) => (Array.isArray(parsed) ? parsed : []);

export type SetVisibleOrHiddenFn = (repoAddresses: RepoAddress[]) => void;

export const useVisibleRepos = (
  allRepos: DagsterRepoOption[],
): {
  visibleRepos: DagsterRepoOption[];
  toggleVisible: SetVisibleOrHiddenFn;
  setVisible: SetVisibleOrHiddenFn;
  setHidden: SetVisibleOrHiddenFn;
} => {
  const {basePath} = React.useContext(AppContext);

  const [hiddenKeys, setHiddenKeys] = useStateWithStorage<string[]>(
    basePath + ':' + HIDDEN_REPO_KEYS,
    validateHiddenKeys,
  );

  const hiddenKeysJSON = JSON.stringify([...hiddenKeys.sort()]);

  const toggleVisible = React.useCallback(
    (repoAddresses: RepoAddress[]) => {
      repoAddresses.forEach((repoAddress) => {
        const key = `${repoAddress.name}:${repoAddress.location}`;

        setHiddenKeys((current) => {
          let nextHiddenKeys = [...(current || [])];
          if (nextHiddenKeys.includes(key)) {
            nextHiddenKeys = nextHiddenKeys.filter((k) => k !== key);
          } else {
            nextHiddenKeys = [...nextHiddenKeys, key];
          }
          return nextHiddenKeys;
        });
      });
    },
    [setHiddenKeys],
  );

  const setVisible = React.useCallback(
    (repoAddresses: RepoAddress[]) => {
      const keysToShow = new Set(
        repoAddresses.map((repoAddress) => `${repoAddress.name}:${repoAddress.location}`),
      );
      setHiddenKeys((current) => {
        return current?.filter((key) => !keysToShow.has(key));
      });
    },
    [setHiddenKeys],
  );

  const setHidden = React.useCallback(
    (repoAddresses: RepoAddress[]) => {
      const keysToHide = new Set(
        repoAddresses.map((repoAddress) => `${repoAddress.name}:${repoAddress.location}`),
      );
      setHiddenKeys((current) => {
        const updatedSet = new Set([...(current || []), ...keysToHide]);
        return Array.from(updatedSet);
      });
    },
    [setHiddenKeys],
  );

  const visibleRepos = React.useMemo(() => {
    // If there's only one repo, skip the local storage check -- we have to show this one.
    if (allRepos.length === 1) {
      return allRepos;
    }
    const hiddenKeys = new Set(JSON.parse(hiddenKeysJSON));
    return allRepos.filter((o) => !hiddenKeys.has(getRepositoryOptionHash(o)));
  }, [allRepos, hiddenKeysJSON]);

  return {visibleRepos, toggleVisible, setVisible, setHidden};
};

/**
 * useCodeLocationFilter returns the single code location the whole UI is scoped to, or `null` for
 * all code locations. The selection lives in localStorage so it survives page switches and reloads.
 * A stored location that is not part of the loaded workspace resolves to `null`, while the
 * workspace is still loading the stored value is kept so pages do not briefly fetch unscoped data.
 */
export const validateCodeLocationFilter = (parsed: unknown) =>
  typeof parsed === 'string' && parsed ? parsed : null;

export const useCodeLocationFilter = (
  locationNames: Set<string>,
  loading: boolean,
): {
  codeLocationFilter: string | null;
  setCodeLocationFilter: (locationName: string | null) => void;
} => {
  const {basePath} = React.useContext(AppContext);

  const [storedFilter, setStoredFilter, clearStoredFilter] = useStateWithStorage<string | null>(
    basePath + ':' + CODE_LOCATION_FILTER_KEY,
    validateCodeLocationFilter,
  );

  const setCodeLocationFilter = React.useCallback(
    (locationName: string | null) =>
      locationName ? setStoredFilter(locationName) : clearStoredFilter(),
    [setStoredFilter, clearStoredFilter],
  );

  const codeLocationFilter =
    storedFilter && (loading || locationNames.has(storedFilter)) ? storedFilter : null;

  return {codeLocationFilter, setCodeLocationFilter};
};

// Public

export const getRepositoryOptionHash = (a: DagsterRepoOption) =>
  `${a.repository.name}:${a.repositoryLocation.name}`;

export const useRepositoryOptions = () => {
  const {allRepos: options, loadingNonAssets: loading} = React.useContext(WorkspaceContext);
  return {options, loading};
};

export const useRepository = (repoAddress: RepoAddress | null | undefined) => {
  const {options} = useRepositoryOptions();
  return findRepositoryAmongOptions(options, repoAddress) || null;
};

export const useJob = (repoAddress: RepoAddress | null | undefined, jobName: string | null) => {
  const repo = useRepository(repoAddress);
  return repo?.repository.pipelines.find((pipelineOrJob) => pipelineOrJob.name === jobName) || null;
};

export const findRepositoryAmongOptions = (
  options: DagsterRepoOption[],
  repoAddress: RepoAddress | null | undefined,
) => {
  return repoAddress
    ? options.find(
        (option) =>
          option.repository.name === repoAddress.name &&
          option.repositoryLocation.name === repoAddress.location,
      )
    : null;
};

export const useActivePipelineForName = (pipelineName: string, snapshotId?: string) => {
  const {options} = useRepositoryOptions();
  const reposWithMatch = findRepoContainingPipeline(options, pipelineName, snapshotId);
  if (reposWithMatch[0]) {
    const match = reposWithMatch[0];
    return match.repository.pipelines.find((pipeline) => pipeline.name === pipelineName) || null;
  }
  return null;
};

export const getFeatureFlagForCodeLocation = (
  locationEntries: WorkspaceLocationNodeFragment[],
  locationName: string,
  flagName: string,
) => {
  const matchingLocation = locationEntries.find(({id}) => id === locationName);
  if (matchingLocation) {
    const {featureFlags} = matchingLocation;
    const matchingFlag = featureFlags.find(({name}) => name === flagName);
    if (matchingFlag) {
      return matchingFlag.enabled;
    }
  }
  return false;
};

export const useFeatureFlagForCodeLocation = (locationName: string, flagName: string) => {
  const {locationEntries} = useContext(WorkspaceContext);
  return getFeatureFlagForCodeLocation(locationEntries, locationName, flagName);
};

export const isThisThingAJob = (repo: DagsterRepoOption | null, pipelineOrJobName: string) => {
  const pipelineOrJob = repo?.repository.pipelines.find(
    (pipelineOrJob) => pipelineOrJob.name === pipelineOrJobName,
  );
  return !!pipelineOrJob?.isJob;
};

export const isThisThingAnAssetJob = (
  repo: DagsterRepoOption | null,
  pipelineOrJobName: string,
) => {
  const pipelineOrJob = repo?.repository.pipelines.find(
    (pipelineOrJob) => pipelineOrJob.name === pipelineOrJobName,
  );
  return !!pipelineOrJob?.isAssetJob;
};

export const isThisThingAnExternalJob = (
  repo: DagsterRepoOption | null,
  pipelineOrJobName: string,
) => {
  const pipelineOrJob = repo?.repository.pipelines.find(
    (pipelineOrJob) => pipelineOrJob.name === pipelineOrJobName,
  );
  return !!pipelineOrJob?.externalJobSource;
};

export const buildPipelineSelector = (
  repoAddress: RepoAddress | null,
  pipelineName: string,
  solidSelection?: string[],
) => {
  const repositorySelector = {
    repositoryName: repoAddress?.name || '',
    repositoryLocationName: repoAddress?.location || '',
  };

  return {
    ...repositorySelector,
    pipelineName,
    solidSelection,
  } as PipelineSelector;
};

export const optionToRepoAddress = (option: DagsterRepoOption) =>
  buildRepoAddress(option.repository.name, option.repository.location.name);

export function repoLocationToRepos(repositoryLocation: RepositoryLocation) {
  return repositoryLocation.repositories.map((repository) => {
    return {repository, repositoryLocation};
  });
}

export function mergeWorkspaceData(
  workspaceLocationEntry: PartialWorkspaceLocationNodeFragment,
  workspaceLocationAssetsEntry: WorkspaceLocationAssetsEntryFragment,
) {
  const {locationOrLoadError, ...rest} = workspaceLocationEntry;
  const result: Partial<WorkspaceLocationNodeFragment> = rest;
  if (locationOrLoadError?.__typename === 'RepositoryLocation') {
    const {repositories, ...rest} = locationOrLoadError;
    result.locationOrLoadError = {
      ...rest,
      repositories: repositories
        ? repositories.map((repo) => {
            const assetsAndGroups = getAssetsAndGroupsByRepo(workspaceLocationAssetsEntry);
            return {
              ...repo,
              ...(assetsAndGroups[repo.id] || {
                assetNodes: [],
                assetGroups: [],
              }),
            };
          })
        : [],
    };
  } else {
    result.locationOrLoadError = locationOrLoadError;
  }

  return result as WorkspaceLocationNodeFragment;
}

function getAssetsAndGroupsByRepo(
  workspaceLocationAssetsEntry: WorkspaceLocationAssetsEntryFragment,
): Record<string, WorkspaceRepositoryAssetsFragment> {
  if (workspaceLocationAssetsEntry.__typename !== 'WorkspaceLocationEntry') {
    return {};
  }

  if (workspaceLocationAssetsEntry.locationOrLoadError?.__typename !== 'RepositoryLocation') {
    return {};
  }

  return workspaceLocationAssetsEntry.locationOrLoadError.repositories.reduce(
    (acc, repo) => {
      acc[repo.id] = repo;
      return acc;
    },
    {} as Record<string, WorkspaceRepositoryAssetsFragment>,
  );
}
