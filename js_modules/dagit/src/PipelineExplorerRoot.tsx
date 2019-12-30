import * as React from "react";
import { match } from "react-router";
import gql from "graphql-tag";
import { History } from "history";
import { useQuery } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";

import Loading from "./Loading";
import PipelineExplorer from "./PipelineExplorer";
import {
  PipelineExplorerRootQuery,
  PipelineExplorerRootQueryVariables
} from "./types/PipelineExplorerRootQuery";

interface IPipelineExplorerRootProps {
  location: { pathname: string };
  match: match<{ 0: string }>;
  history: History<any>;
}

const PipelineExplorerRoot: React.FunctionComponent<IPipelineExplorerRootProps> = props => {
  const [pipelineSelector, ...pathSolids] = props.match.params["0"].split("/");
  const [pipelineName, query] = [...pipelineSelector.split(":"), ""];

  const parentNames = pathSolids.slice(0, pathSolids.length - 1);
  const selectedName = pathSolids[pathSolids.length - 1];

  const queryResult = useQuery<
    PipelineExplorerRootQuery,
    PipelineExplorerRootQueryVariables
  >(PIPELINE_EXPLORER_ROOT_QUERY, {
    fetchPolicy: "cache-and-network",
    partialRefetch: true,
    variables: {
      pipeline: pipelineName,
      parentHandleID: parentNames.join(".")
    }
  });

  return (
    <Loading<PipelineExplorerRootQuery> queryResult={queryResult}>
      {({ pipelineOrError }) => {
        switch (pipelineOrError.__typename) {
          case "PipelineNotFoundError":
            return (
              <NonIdealState
                icon={IconNames.FLOW_BRANCH}
                title="Pipeline Not Found"
                description={pipelineOrError.message}
              />
            );
          case "InvalidSubsetError":
          case "PythonError":
            return <NonIdealState icon={IconNames.ERROR} title="Query Error" />;
          default:
            const pipeline = pipelineOrError;
            const displayedHandles = pipeline.solidHandles;
            const parentSolidHandle = pipelineOrError.solidHandle;
            return (
              <PipelineExplorer
                history={props.history}
                path={pathSolids}
                visibleSolidsQuery={query}
                pipeline={pipelineOrError}
                handles={displayedHandles}
                parentHandle={parentSolidHandle ? parentSolidHandle : undefined}
                selectedHandle={displayedHandles.find(
                  h => h.solid.name === selectedName
                )}
                getInvocations={definitionName =>
                  displayedHandles
                    .filter(s => s.solid.definition.name === definitionName)
                    .map(s => ({ handleID: s.handleID }))
                }
              />
            );
        }
      }}
    </Loading>
  );
};

export const PIPELINE_EXPLORER_ROOT_QUERY = gql`
  query PipelineExplorerRootQuery(
    $pipeline: String!
    $parentHandleID: String!
  ) {
    pipelineOrError(params: { name: $pipeline }) {
      ... on PipelineReference {
        name
      }
      ... on Pipeline {
        ...PipelineExplorerFragment

        solidHandle(handleID: $parentHandleID) {
          ...PipelineExplorerParentSolidHandleFragment
        }
        solidHandles(parentHandleID: $parentHandleID) {
          handleID
          solid {
            name
          }
          ...PipelineExplorerSolidHandleFragment
        }
      }
      ... on PipelineNotFoundError {
        message
      }
    }
  }
  ${PipelineExplorer.fragments.PipelineExplorerFragment}
  ${PipelineExplorer.fragments.PipelineExplorerSolidHandleFragment}
  ${PipelineExplorer.fragments.PipelineExplorerParentSolidHandleFragment}
`;

export default PipelineExplorerRoot;
