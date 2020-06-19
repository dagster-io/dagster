import * as React from "react";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import {
  RootRepositoriesQuery,
  RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes,
  RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location
} from "./types/RootRepositoriesQuery";
import PythonErrorInfo from "./PythonErrorInfo";

type Repository = RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes;
type RepositoryLocation = RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location;

export interface DagsterRepoOption {
  repositoryLocation: RepositoryLocation;
  repository: Repository;
}

export const DagsterRepositoryContext = React.createContext<DagsterRepoOption>(
  new Error("DagsterRepositoryContext should never be uninitialized") as any
);

export const ROOT_REPOSITORIES_QUERY = gql`
  query RootRepositoriesQuery {
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          name
          pipelines {
            name
          }
          location {
            name
            isReloadSupported
            environmentPath
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

  if (!data || !data.repositoriesOrError) {
    return { options: [], error: null };
  }
  if (data.repositoriesOrError.__typename === "PythonError") {
    return { options: [], error: data.repositoriesOrError };
  }

  const options: DagsterRepoOption[] = data.repositoriesOrError.nodes.map(
    repository => ({
      repository,
      repositoryLocation: repository.location
    })
  );

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
  pipelineName: string,
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
