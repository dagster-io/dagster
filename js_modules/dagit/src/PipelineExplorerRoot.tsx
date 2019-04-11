import * as React from "react";
import { match } from "react-router";
import gql from "graphql-tag";
import { History } from "history";
import { QueryResult, Query } from "react-apollo";

import Loading from "./Loading";
import PipelineExplorer from "./PipelineExplorer";
import { PipelineExplorerRootQuery } from "./types/PipelineExplorerRootQuery";

interface IPipelineExplorerRootProps {
  match: match<{ pipelineName: string; solidName: string }>;
  history: History<any>;
}

export default class PipelineExplorerRoot extends React.Component<
  IPipelineExplorerRootProps
> {
  render() {
    const { pipelineName, solidName } = this.props.match.params;

    return (
      <Query
        query={PIPELINE_EXPLORER_ROOT_QUERY}
        fetchPolicy="cache-and-network"
        partialRefetch={true}
        variables={{ name: pipelineName }}
      >
        {(queryResult: QueryResult<PipelineExplorerRootQuery, any>) => (
          <Loading queryResult={queryResult}>
            {result => (
              <PipelineExplorer
                history={this.props.history}
                pipeline={result.pipeline}
                solid={
                  solidName
                    ? result.pipeline.solids.find(s => s.name === solidName)
                    : undefined
                }
              />
            )}
          </Loading>
        )}
      </Query>
    );
  }
}

export const PIPELINE_EXPLORER_ROOT_QUERY = gql`
  query PipelineExplorerRootQuery($name: String!) {
    pipeline(params: { name: $name }) {
      name
      ...PipelineExplorerFragment
      solids {
        ...PipelineExplorerSolidFragment
      }
    }
  }

  ${PipelineExplorer.fragments.PipelineExplorerFragment}
  ${PipelineExplorer.fragments.PipelineExplorerSolidFragment}
`;
