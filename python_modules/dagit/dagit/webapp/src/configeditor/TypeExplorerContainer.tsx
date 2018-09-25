import * as React from "react";
import gql from "graphql-tag";
import Loading from "../Loading";
import { Query, QueryResult } from "react-apollo";
import TypeExplorer from "./TypeExplorer";
import { TypeExplorerContainerQuery } from "./types/TypeExplorerContainerQuery";

interface ITypeExplorerContainerProps {
  pipelineName: string;
  typePath: string;
}

export default class TypeExplorerContainer extends React.Component<
  ITypeExplorerContainerProps,
  {}
> {
  render() {
    return (
      <Query
        query={TYPE_EXPLORER_CONTAINER_QUERY}
        variables={{
          pipelineName: this.props.pipelineName,
          typePath: this.props.typePath
        }}
      >
        {(
          queryResult: QueryResult<
            TypeExplorerContainerQuery,
            { pipelineName: string; typePath: string }
          >
        ) => {
          return (
            <Loading queryResult={queryResult}>
              {data => {
                if (data.type) {
                  return <TypeExplorer type={data.type} />;
                } else {
                  return <div>Type Not Found</div>;
                }
              }}
            </Loading>
          );
        }}
      </Query>
    );
  }
}

export const TYPE_EXPLORER_CONTAINER_QUERY = gql`
  query TypeExplorerContainerQuery($pipelineName: String!, $typePath: String!) {
    type(pipelineName: $pipelineName, typePath: $typePath) @client {
      ...TypeExplorerFragment
    }
  }

  ${TypeExplorer.fragments.TypeExplorerFragment}
`;
