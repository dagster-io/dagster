import * as React from "react";
import gql from "graphql-tag";
import Loading from "../Loading";
import { useQuery } from "react-apollo";
import TypeExplorer from "./TypeExplorer";
import {
  TypeExplorerContainerQuery,
  TypeExplorerContainerQueryVariables
} from "./types/TypeExplorerContainerQuery";
import { PipelineSelector } from "../PipelineSelectorUtils";

interface ITypeExplorerContainerProps {
  selector: PipelineSelector;
  typeName: string;
}

export const TypeExplorerContainer: React.FunctionComponent<ITypeExplorerContainerProps> = ({
  selector,
  typeName
}) => {
  const queryResult = useQuery<
    TypeExplorerContainerQuery,
    TypeExplorerContainerQueryVariables
  >(TYPE_EXPLORER_CONTAINER_QUERY, {
    fetchPolicy: "cache-and-network",
    variables: {
      pipelineName: selector.pipelineName,
      runtimeTypeName: typeName
    }
  });
  return (
    <Loading queryResult={queryResult}>
      {data => {
        if (
          data.pipeline &&
          data.pipeline.runtimeTypeOrError &&
          data.pipeline.runtimeTypeOrError.__typename === "RegularRuntimeType"
        ) {
          return <TypeExplorer type={data.pipeline.runtimeTypeOrError} />;
        } else {
          return <div>Type Not Found</div>;
        }
      }}
    </Loading>
  );
};

export const TYPE_EXPLORER_CONTAINER_QUERY = gql`
  query TypeExplorerContainerQuery(
    $pipelineName: String!
    $runtimeTypeName: String!
  ) {
    pipeline(params: { name: $pipelineName }) {
      runtimeTypeOrError(runtimeTypeName: $runtimeTypeName) {
        __typename
        ... on RegularRuntimeType {
          ...TypeExplorerFragment
        }
      }
    }
  }
  ${TypeExplorer.fragments.TypeExplorerFragment}
`;
