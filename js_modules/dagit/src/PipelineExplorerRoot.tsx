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
  PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles
} from "./types/PipelineExplorerRootQuery";

type Handle = PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles;

interface IPipelineExplorerRootProps {
  location: { pathname: string };
  match: match<{ pipelineName: string; 0: string }>;
  history: History<any>;
}

const PipelineExplorerRoot: React.FunctionComponent<IPipelineExplorerRootProps> = props => {
  const queryResult = useQuery<PipelineExplorerRootQuery>(
    PIPELINE_EXPLORER_ROOT_QUERY,
    {
      fetchPolicy: "cache-and-network",
      partialRefetch: true,
      variables: { name: props.match.params.pipelineName }
    }
  );
  const urlPathParts = props.match.params["0"];
  const solidPath = urlPathParts.startsWith("/")
    ? urlPathParts.slice(1)
    : urlPathParts; // from the React Router regex
  const pathSolids = solidPath.split("/");
  const parentNames = pathSolids.slice(0, pathSolids.length - 1);
  const selectedName = pathSolids[pathSolids.length - 1];

  return (
    <Loading queryResult={queryResult}>
      {result => {
        const pipelineOrError = result.pipelineOrError;

        switch (pipelineOrError.__typename) {
          case "PipelineNotFoundError":
            return (
              <NonIdealState
                icon={IconNames.FLOW_BRANCH}
                title="Pipeline Not Found"
                description={pipelineOrError.message}
              />
            );
          case "Pipeline":
            const pipeline = pipelineOrError;
            let displayedHandles = pipeline.solidHandles.filter(h => !h.parent);
            let parentHandle: Handle | undefined;

            const nameMatch = (parentName: string) => (h: Handle) =>
              h.solid.name === parentName;

            const filterHandle = (parent: Handle | undefined) => (h: Handle) =>
              h.parent && parent && h.parent.handleID === parent.handleID;

            for (const parentName of parentNames) {
              parentHandle = displayedHandles.find(nameMatch(parentName));
              displayedHandles = pipeline.solidHandles.filter(
                filterHandle(parentHandle)
              );
            }
            const selectedHandle = displayedHandles.find(
              h => h.solid.name === selectedName
            );

            return (
              <PipelineExplorer
                history={props.history}
                path={pathSolids}
                pipeline={pipeline}
                handles={displayedHandles}
                parentHandle={parentHandle}
                selectedHandle={selectedHandle}
                getInvocations={definitionName =>
                  pipeline.solidHandles
                    .filter(s => s.solid.definition.name === definitionName)
                    .map(s => ({ handleID: s.handleID }))
                }
              />
            );

          default:
            return null;
        }
      }}
    </Loading>
  );
};

export const PIPELINE_EXPLORER_ROOT_QUERY = gql`
  query PipelineExplorerRootQuery($name: String!) {
    pipelineOrError(params: { name: $name }) {
      ... on PipelineReference {
        name
      }
      ... on Pipeline {
        ...PipelineExplorerFragment
        solids {
          name
        }
        solidHandles {
          handleID
          parent {
            handleID
          }
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
`;

export default PipelineExplorerRoot;
