import gql from "graphql-tag";
import * as React from "react";
import Loading from "../Loading";
import { useQuery } from "react-apollo";
import TypeList from "./TypeList";
import { TypeListContainerQuery } from "./types/TypeListContainerQuery";
import { PipelineSelector } from "../leftnav/PipelineSelectorUtils";

interface ITypeListContainerProps {
  selector: PipelineSelector;
}

export const TypeListContainer: React.FunctionComponent<ITypeListContainerProps> = ({
  selector
}) => {
  const queryResult = useQuery<TypeListContainerQuery>(
    TYPE_LIST_CONTAINER_QUERY,
    {
      fetchPolicy: "cache-and-network",
      variables: {
        pipelineName: selector.pipelineName
      }
    }
  );

  return (
    <Loading queryResult={queryResult}>
      {data => {
        if (data.pipelineOrError.__typename === "Pipeline") {
          return <TypeList types={data.pipelineOrError.dagsterTypes} />;
        } else {
          return null;
        }
      }}
    </Loading>
  );
};

export const TYPE_LIST_CONTAINER_QUERY = gql`
  query TypeListContainerQuery($pipelineName: String!) {
    pipelineOrError(params: { name: $pipelineName }) {
      __typename
      ... on Pipeline {
        name
        dagsterTypes {
          ...TypeListFragment
        }
      }
    }
  }

  ${TypeList.fragments.TypeListFragment}
`;
