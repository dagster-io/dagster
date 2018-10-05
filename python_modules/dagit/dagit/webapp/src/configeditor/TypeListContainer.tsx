import * as React from "react";
import gql from "graphql-tag";
import Loading from "../Loading";
import { Query, QueryResult } from "react-apollo";
import TypeList from "./TypeList";
import { TypeListContainerQuery } from "./types/TypeListContainerQuery";

interface ITypeListContainerProps {
  pipelineName: string;
}

export default class TypeListContainer extends React.Component<
  ITypeListContainerProps,
  {}
> {
  render() {
    return (
      <Query
        query={TYPE_LIST_CONTAINER_QUERY}
        variables={{
          pipelineName: this.props.pipelineName
        }}
      >
        {(
          queryResult: QueryResult<
            TypeListContainerQuery,
            { pipelineName: string }
          >
        ) => {
          return (
            <Loading queryResult={queryResult}>
              {data => {
                return <TypeList types={data.types} />;
              }}
            </Loading>
          );
        }}
      </Query>
    );
  }
}

export const TYPE_LIST_CONTAINER_QUERY = gql`
  query TypeListContainerQuery($pipelineName: String!) {
    types(pipelineName: $pipelineName) {
      ...TypeListFragment
    }
  }

  ${TypeList.fragments.TypeListFragment}
`;
