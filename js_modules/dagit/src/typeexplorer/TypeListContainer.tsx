import gql from "graphql-tag";
import * as React from "react";
import styled from "styled-components";
import Loading from "../Loading";
import { useQuery } from "react-apollo";
import TypeList from "./TypeList";
import { TypeListContainerQuery } from "./types/TypeListContainerQuery";

interface ITypeListContainerProps {
  pipelineName: string;
}

export const TypeListContainer: React.FunctionComponent<
  ITypeListContainerProps
> = ({ pipelineName }) => {
  const queryResult = useQuery<TypeListContainerQuery>(
    TYPE_LIST_CONTAINER_QUERY,
    {
      fetchPolicy: "cache-and-network",
      variables: {
        pipelineName: pipelineName
      }
    }
  );

  return (
    <Loading queryResult={queryResult}>
      {data => {
        if (data.pipelineOrError.__typename === "Pipeline") {
          return (
            <TypeListWrapper>
              <TypeList types={data.pipelineOrError.runtimeTypes} />
            </TypeListWrapper>
          );
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
        runtimeTypes {
          ...TypeListFragment
        }
      }
    }
  }

  ${TypeList.fragments.TypeListFragment}
`;

const TypeListWrapper = styled.div`
  padding: 5px;
`;
