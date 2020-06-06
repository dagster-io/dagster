import * as React from "react";
import gql from "graphql-tag";
import {
  RepositoryLocationFragment,
  RepositoryLocationFragment_repositories
} from "./types/RepositoryLocationFragment";

export interface IDagsterRepositoryContext {
  repositoryLocation?: RepositoryLocationFragment;
  repository?: RepositoryLocationFragment_repositories;
}

export const DagsterRepositoryContext = React.createContext<
  IDagsterRepositoryContext
>({});
export const REPOSITORY_LOCATION_FRAGMENT = gql`
  fragment RepositoryLocationFragment on RepositoryLocation {
    name
    repositories {
      name
      pipelines {
        name
      }
    }
  }
`;

export const usePipelineSelector = (
  pipelineName?: string,
  solidSelection?: string[]
) => {
  const { repository, repositoryLocation } = React.useContext(
    DagsterRepositoryContext
  );

  if (!repository || !repositoryLocation) {
    // use legacy fields
    console.error("Using legacy pipeline selector", pipelineName);
    return {
      name: pipelineName,
      solidSelection
    };
  }

  return {
    pipelineName,
    repositoryLocationName: repositoryLocation?.name,
    repositoryName: repository?.name,
    solidSelection
  };
};
