import * as React from "react";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import {
  RootRepositoriesQuery,
  RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes,
  RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_repositories
} from "./types/RootRepositoriesQuery";
import PythonErrorInfo from "./PythonErrorInfo";

export interface DagsterRepoOption {
  repositoryLocation: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes;
  repository: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_repositories;
}

export const DagsterRepositoryContext = React.createContext<DagsterRepoOption>(
  new Error("DagsterRepositoryContext should never be uninitialized") as any
);

export const ROOT_REPOSITORIES_QUERY = gql`
  query RootRepositoriesQuery {
    repositoryLocationsOrError {
      __typename
      ... on RepositoryLocationConnection {
        nodes {
          name
          repositories {
            name
            pipelines {
              name
            }
          }
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
`;

export const isRepositoryOptionEqual = (
  a: DagsterRepoOption,
  b: DagsterRepoOption
) =>
  a.repository.name === b.repository.name &&
  a.repositoryLocation.name === b.repositoryLocation.name
    ? true
    : false;

export const useRepositoryOptions = () => {
  const { data } = useQuery<RootRepositoriesQuery>(ROOT_REPOSITORIES_QUERY, {
    fetchPolicy: "cache-and-network"
  });

  const options: DagsterRepoOption[] = [];

  if (!data || !data.repositoryLocationsOrError) {
    return { options, error: null };
  }
  if (data.repositoryLocationsOrError.__typename === "PythonError") {
    return { options, error: data.repositoryLocationsOrError };
  }

  for (const repositoryLocation of data.repositoryLocationsOrError.nodes) {
    for (const repository of repositoryLocation.repositories) {
      options.push({ repository, repositoryLocation });
    }
  }

  return { error: null, options };
};

export const useRepositorySelector = () => {
  const { repository, repositoryLocation } = React.useContext(
    DagsterRepositoryContext
  );

  if (!repository || !repositoryLocation) {
    // use legacy fields
    throw Error("no legacy repository");
  }

  return {
    repositoryLocationName: repositoryLocation.name,
    repositoryName: repository.name
  };
};

export const usePipelineSelector = (
  pipelineName?: string,
  solidSelection?: string[]
) => {
  const repositorySelector = useRepositorySelector();
  return {
    ...repositorySelector,
    pipelineName,
    solidSelection
  };
};

export const useScheduleSelector = (scheduleName: string) => {
  const repositorySelector = useRepositorySelector();
  return {
    ...repositorySelector,
    scheduleName
  };
};
