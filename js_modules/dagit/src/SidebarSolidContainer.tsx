import * as React from 'react';
import {SidebarSolidInvocation} from './SidebarSolidInvocation';
import {SidebarSolidDefinition} from './SidebarSolidDefinition';
import {SidebarTabbedContainerSolidQuery} from './types/SidebarTabbedContainerSolidQuery';
import {SolidNameOrPath} from './PipelineExplorer';
import {useQuery} from 'react-apollo';
import Loading from './Loading';
import gql from 'graphql-tag';
import {PipelineExplorerPath} from './PipelinePathUtils';
import {usePipelineSelector} from './DagsterRepositoryContext';

interface SidebarSolidContainerProps {
  handleID: string;
  explorerPath: PipelineExplorerPath;
  showingSubsolids: boolean;
  parentSolidHandleID?: string;
  getInvocations?: (definitionName: string) => {handleID: string}[];
  onEnterCompositeSolid: (arg: SolidNameOrPath) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
}

export const SidebarSolidContainer: React.FunctionComponent<SidebarSolidContainerProps> = ({
  handleID,
  explorerPath,
  getInvocations,
  showingSubsolids,
  onEnterCompositeSolid,
  onClickSolid,
}) => {
  const pipelineSelector = usePipelineSelector(explorerPath.pipelineName);
  const queryResult = useQuery<SidebarTabbedContainerSolidQuery>(
    SIDEBAR_TABBED_CONTAINER_SOLID_QUERY,
    {
      variables: {selector: pipelineSelector, handleID: handleID},
      fetchPolicy: 'cache-and-network',
    },
  );

  return (
    <Loading queryResult={queryResult}>
      {({pipelineOrError}) => {
        if (pipelineOrError?.__typename !== 'Pipeline') {
          // should not reach here, unless the pipeline loads and then does not load in subsequent
          // requests
          console.error('Could not load pipeline solids');
          return <span>Could not load pipeline solids.</span>;
        }
        return (
          <>
            <SidebarSolidInvocation
              key={`${handleID}-inv`}
              solid={pipelineOrError!.solidHandle!.solid}
              onEnterCompositeSolid={
                pipelineOrError!.solidHandle!.solid.definition.__typename ===
                'CompositeSolidDefinition'
                  ? onEnterCompositeSolid
                  : undefined
              }
            />
            <SidebarSolidDefinition
              key={`${handleID}-def`}
              showingSubsolids={showingSubsolids}
              definition={pipelineOrError!.solidHandle!.solid.definition}
              getInvocations={getInvocations}
              onClickInvocation={({handleID}) => onClickSolid({path: handleID.split('.')})}
            />
          </>
        );
      }}
    </Loading>
  );
};

export const SIDEBAR_TABBED_CONTAINER_SOLID_QUERY = gql`
  query SidebarTabbedContainerSolidQuery($selector: PipelineSelector!, $handleID: String!) {
    pipelineOrError(params: $selector) {
      __typename
      ... on Pipeline {
        id
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
  }
  ${SidebarSolidInvocation.fragments.SidebarSolidInvocationFragment}
  ${SidebarSolidDefinition.fragments.SidebarSolidDefinitionFragment}
`;
