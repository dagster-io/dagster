import * as React from "react";
import { match } from "react-router";
import gql from "graphql-tag";
import { History } from "history";
import { QueryResult, Query } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";

import Loading from "./Loading";
import PipelineExplorer from "./PipelineExplorer";
import {
  PipelineExplorerRootQuery,
  PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles
} from "./types/PipelineExplorerRootQuery";

interface IPipelineExplorerRootProps {
  location: { pathname: string };
  match: match<{ pipelineName: string; solidName: string }>;
  history: History<any>;
}

const PipelineExplorerRoot: React.FunctionComponent<
  IPipelineExplorerRootProps
> = props => {
  const pathSolids = props.location.pathname
    .split(/\/explore\/?/)
    .pop()!
    .split("/");
  const parentNames = pathSolids.slice(0, pathSolids.length - 1);
  const selectedName = pathSolids[pathSolids.length - 1];

  return (
    <Query
      query={PIPELINE_EXPLORER_ROOT_QUERY}
      fetchPolicy="cache-and-network"
      partialRefetch={true}
      variables={{ name: props.match.params.pipelineName }}
    >
      {(queryResult: QueryResult<PipelineExplorerRootQuery, any>) => (
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
                let displayedHandles = pipeline.solidHandles.filter(
                  h => !h.parent
                );
                let parent:
                  | PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles
                  | undefined;

                for (const parentName of parentNames) {
                  parent = displayedHandles.find(
                    h => h.solid.name === parentName
                  );
                  displayedHandles = pipeline.solidHandles.filter(
                    h =>
                      h.parent &&
                      parent &&
                      h.parent.handleID === parent.handleID
                  );
                }
                const selectedHandle = displayedHandles.find(
                  h => h.solid.name === selectedName
                );
                const selectedDefinitionInvocations =
                  selectedHandle &&
                  pipeline.solidHandles.filter(
                    s =>
                      s.solid.definition.name ===
                      selectedHandle.solid.definition.name
                  );

                return (
                  <PipelineExplorer
                    history={props.history}
                    path={pathSolids}
                    pipeline={pipeline}
                    handles={displayedHandles}
                    parentHandle={parent}
                    selectedDefinitionInvocations={
                      selectedDefinitionInvocations
                    }
                    selectedHandle={selectedHandle}
                  />
                );

              default:
                return null;
            }
          }}
        </Loading>
      )}
    </Query>
  );
};

export const PIPELINE_EXPLORER_ROOT_QUERY = gql`
  query PipelineExplorerRootQuery($name: String!) {
    pipelineOrError(params: { name: $name }) {
      ... on Pipeline {
        name
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
