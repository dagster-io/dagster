import * as React from "react";
import { match } from "react-router";
import gql from "graphql-tag";
import { History } from "history";
import { QueryResult, Query } from "react-apollo";

import Loading from "./Loading";
import PipelineExplorer from "./PipelineExplorer";
import { PipelineExplorerRootQuery } from "./types/PipelineExplorerRootQuery";

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
  const parentHandleID = pathSolids[pathSolids.length - 2];
  const selectedHandleID = pathSolids[pathSolids.length - 1];

  return (
    <Query
      query={PIPELINE_EXPLORER_ROOT_QUERY}
      fetchPolicy="cache-and-network"
      partialRefetch={true}
      variables={{ name: props.match.params.pipelineName }}
    >
      {(queryResult: QueryResult<PipelineExplorerRootQuery, any>) => (
        <Loading queryResult={queryResult}>
          {({ pipeline }) => {
            let displayedHandles = pipeline.solidHandles.filter(h => !h.parent);
            let parent = undefined;

            if (parentHandleID) {
              parent = pipeline.solidHandles.find(
                h => h.handleID === parentHandleID
              );
              displayedHandles = pipeline.solidHandles.filter(
                h => h.parent && h.parent.handleID === parentHandleID
              );
            }

            return (
              <PipelineExplorer
                history={props.history}
                path={pathSolids}
                pipeline={pipeline}
                handles={displayedHandles}
                parentHandle={parent}
                selectedHandle={displayedHandles.find(
                  h => h.handleID === selectedHandleID
                )}
              />
            );
          }}
        </Loading>
      )}
    </Query>
  );
};

export const PIPELINE_EXPLORER_ROOT_QUERY = gql`
  query PipelineExplorerRootQuery($name: String!) {
    pipeline(params: { name: $name }) {
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
  }

  ${PipelineExplorer.fragments.PipelineExplorerFragment}
  ${PipelineExplorer.fragments.PipelineExplorerSolidHandleFragment}
`;

export default PipelineExplorerRoot;
