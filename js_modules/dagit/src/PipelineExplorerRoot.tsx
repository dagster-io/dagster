import * as React from "react";
import { uniqBy } from "lodash";
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
    .substr(props.location.pathname.indexOf("explore") + 8)
    .split("/");
  const parentSolidName = pathSolids[pathSolids.length - 2];
  const selectedSolidName = pathSolids[pathSolids.length - 1];

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
            let names = pipeline.solids.map(s => s.name);
            let parent = undefined;

            if (parentSolidName) {
              parent = pipeline.solidHandles.find(
                h => h.solid.name === parentSolidName
              )!.solid;
              if (parent.definition.__typename === "CompositeSolidDefinition") {
                names = parent.definition.solids.map(s => s.name);
              }
            }

            let solids = pipeline.solidHandles
              .filter(h => names.includes(h.solid.name))
              .map(h => h.solid);

            // TODO: Currently solidHandles returns lots of duplicate entries
            solids = uniqBy(solids, a => a.name);

            const selected = selectedSolidName
              ? solids.find(s => s.name === selectedSolidName)
              : undefined;

            return (
              <PipelineExplorer
                history={props.history}
                path={pathSolids}
                pipeline={pipeline}
                solids={solids}
                solid={selected}
                parentSolid={parent}
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
        solid {
          name
          ...PipelineExplorerSolidFragment
          definition {
            __typename
            ... on CompositeSolidDefinition {
              solids {
                name
              }
            }
          }
        }
      }
    }
  }

  ${PipelineExplorer.fragments.PipelineExplorerFragment}
  ${PipelineExplorer.fragments.PipelineExplorerSolidFragment}
`;

export default PipelineExplorerRoot;
