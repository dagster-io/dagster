import * as React from "react";
import { SidebarSolidInvocation } from "./SidebarSolidInvocation";
import { SidebarSolidDefinition } from "./SidebarSolidDefinition";
import { SidebarTabbedContainerSolidQuery } from "./types/SidebarTabbedContainerSolidQuery";
import { SolidNameOrPath } from "./PipelineExplorer";
import { useQuery } from "react-apollo";
import Loading from "./Loading";
import gql from "graphql-tag";

interface SidebarSolidContainerProps {
  handleID: string;
  pipelineName: string;
  showingSubsolids: boolean;
  parentSolidHandleID?: string;
  getInvocations?: (definitionName: string) => { handleID: string }[];
  onEnterCompositeSolid: (arg: SolidNameOrPath) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
}

export const SidebarSolidContainer: React.FunctionComponent<SidebarSolidContainerProps> = ({
  handleID,
  pipelineName,
  getInvocations,
  showingSubsolids,
  onEnterCompositeSolid,
  onClickSolid
}) => {
  const queryResult = useQuery<SidebarTabbedContainerSolidQuery>(
    SIDEBAR_TABBED_CONTAINER_SOLID_QUERY,
    {
      variables: { pipeline: pipelineName, handleID: handleID },
      fetchPolicy: "cache-and-network"
    }
  );

  return (
    <Loading queryResult={queryResult}>
      {({ pipeline }) =>
        pipeline ? (
          <>
            <SidebarSolidInvocation
              key={`${handleID}-inv`}
              solid={pipeline!.solidHandle!.solid}
              onEnterCompositeSolid={
                pipeline!.solidHandle!.solid.definition.__typename ===
                "CompositeSolidDefinition"
                  ? onEnterCompositeSolid
                  : undefined
              }
            />
            <SidebarSolidDefinition
              key={`${handleID}-def`}
              showingSubsolids={showingSubsolids}
              definition={pipeline!.solidHandle!.solid.definition}
              getInvocations={getInvocations}
              onClickInvocation={({ handleID }) =>
                onClickSolid({ path: handleID.split(".") })
              }
            />
          </>
        ) : (
          <span />
        )
      }
    </Loading>
  );
};

export const SIDEBAR_TABBED_CONTAINER_SOLID_QUERY = gql`
  query SidebarTabbedContainerSolidQuery(
    $pipeline: String!
    $handleID: String!
  ) {
    pipeline(params: { name: $pipeline }) {
      name
      solidHandle(handleID: $handleID) {
        solid {
          ...SidebarSolidInvocationFragment

          definition {
            __typename
            ...SidebarSolidDefinitionFragment
          }
        }
      }
    }
  }
  ${SidebarSolidInvocation.fragments.SidebarSolidInvocationFragment}
  ${SidebarSolidDefinition.fragments.SidebarSolidDefinitionFragment}
`;
