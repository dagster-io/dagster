import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {RepositoryInformationFragment} from 'src/RepositoryInformation';
import {InstanceExecutableQuery} from 'src/types/InstanceExecutableQuery';
import {
  RootRepositoriesQuery,
  RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes,
  RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location,
} from 'src/types/RootRepositoriesQuery';
import {RepositorySelector} from 'src/types/globalTypes';

export type Repository = RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes;
export type RepositoryLocation = RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location;

export interface DagsterRepoOption {
  repositoryLocation: RepositoryLocation;
  repository: Repository;
}

export const repositorySelectorFromDagsterRepoOption = (
  dagsterRepoOption: DagsterRepoOption,
): RepositorySelector => {
  const {repository} = dagsterRepoOption;

  return {
    repositoryLocationName: repository.location.name,
    repositoryName: repository.name,
  };
};

const LAST_REPO_KEY = 'dagit.last-repo';

export const DagsterRepositoryContext = React.createContext<DagsterRepoOption | null>(
  new Error('DagsterRepositoryContext should never be uninitialized') as any,
);

export const ROOT_REPOSITORIES_QUERY = gql`
  query RootRepositoriesQuery {
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          id
          name
          pipelines {
            name
            pipelineSnapshotId
          }
          partitionSets {
            pipelineName
          }
          location {
            name
            isReloadSupported
            environmentPath
          }
          ...RepositoryInfoFragment
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${RepositoryInformationFragment}
`;

export const getRepositoryOptionHash = (a: DagsterRepoOption) =>
  `${a.repository.name}:${a.repositoryLocation.name}`;

export const isRepositoryOptionEqual = (a: DagsterRepoOption, b: DagsterRepoOption) =>
  getRepositoryOptionHash(a) === getRepositoryOptionHash(b);

/**
 * useRepositoryOptions vends the set of available repositories by fetching them via GraphQL
 * and coercing the response to the DagsterRepoOption[] type.
 */
export const useRepositoryOptions = () => {
  const {data, loading} = useQuery<RootRepositoriesQuery>(ROOT_REPOSITORIES_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  let options: DagsterRepoOption[] = [];
  if (!data || !data.repositoriesOrError) {
    return {options, loading, error: null};
  }
  if (data.repositoriesOrError.__typename === 'PythonError') {
    return {options, loading, error: data.repositoriesOrError};
  }

  options = data.repositoriesOrError.nodes.map((repository) => ({
    repository,
    repositoryLocation: repository.location,
  }));

  return {error: null, loading, options};
};

/**
 * useCurrentRepositoryState vends `[repo, setRepo]` and internally mirrors the current
 * selection into localStorage so that the default selection in new browser windows
 * is the repo currently active in your session.
 */
export const useCurrentRepositoryState = (options: DagsterRepoOption[]) => {
  const [repoKey, setRepoKey] = React.useState<string | null>(null);

  const setRepo = (next: DagsterRepoOption) => {
    const key = getRepositoryOptionHash(next);
    window.localStorage.setItem(LAST_REPO_KEY, key);
    setRepoKey(key);
  };

  // If the selection is null or the selected repository cannot be found in the set,
  // coerce the selection to the last used repo or [0].
  React.useEffect(() => {
    if (
      options.length &&
      (!repoKey || !options.some((o) => getRepositoryOptionHash(o) === repoKey))
    ) {
      const lastKey = window.localStorage.getItem(LAST_REPO_KEY);
      const last = lastKey && options.find((o) => getRepositoryOptionHash(o) === lastKey);
      setRepoKey(getRepositoryOptionHash(last || options[0]));
    }
  }, [repoKey, options]);

  const repoForKey = options.find((o) => getRepositoryOptionHash(o) === repoKey) || null;
  return [repoForKey, setRepo] as [typeof repoForKey, typeof setRepo];
};

export const useRepositorySelector = (): RepositorySelector => {
  const repository = useRepository();
  return {
    repositoryLocationName: repository?.location.name || '',
    repositoryName: repository?.name || '',
  };
};

export const useRepository = () => {
  const repoContext = React.useContext(DagsterRepositoryContext);
  return repoContext?.repository;
};

export const useActivePipelineForName = (pipelineName: string) => {
  const repository = useRepository();
  return repository?.pipelines.find((pipeline) => pipeline.name === pipelineName) || null;
};

export const usePipelineSelector = (pipelineName: string, solidSelection?: string[]) => {
  const repositorySelector = useRepositorySelector();
  return {
    ...repositorySelector,
    pipelineName,
    solidSelection,
  };
};

export const useScheduleSelector = (scheduleName: string) => {
  const repositorySelector = useRepositorySelector();
  return {
    ...repositorySelector,
    scheduleName,
  };
};

export const INSTANCE_EXECUTABLE_QUERY = gql`
  query InstanceExecutableQuery {
    instance {
      executablePath
    }
  }
`;
export const useDagitExecutablePath = () => {
  const {data} = useQuery<InstanceExecutableQuery>(INSTANCE_EXECUTABLE_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  return data?.instance.executablePath;
};

export const scheduleSelectorWithRepository = (
  scheduleName: string,
  repositorySelector?: RepositorySelector,
) => {
  return {
    ...repositorySelector,
    scheduleName,
  };
};
