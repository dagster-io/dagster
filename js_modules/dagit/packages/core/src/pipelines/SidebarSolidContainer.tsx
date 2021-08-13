import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {SolidNameOrPath} from '../solids/SolidNameOrPath';
import {Loading} from '../ui/Loading';
import {usePipelineSelector} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {PipelineExplorerPath} from './PipelinePathUtils';
import {SidebarSolidDefinition, SIDEBAR_SOLID_DEFINITION_FRAGMENT} from './SidebarSolidDefinition';
import {SidebarSolidInvocation, SIDEBAR_SOLID_INVOCATION_FRAGMENT} from './SidebarSolidInvocation';
import {SidebarTabbedContainerSolidQuery} from './types/SidebarTabbedContainerSolidQuery';

interface SidebarSolidContainerProps {
  handleID: string;
  explorerPath: PipelineExplorerPath;
  showingSubsolids: boolean;
  parentSolidHandleID?: string;
  getInvocations?: (definitionName: string) => {handleID: string}[];
  onEnterCompositeSolid: (arg: SolidNameOrPath) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
  repoAddress?: RepoAddress;
}

export const SidebarSolidContainer: React.FC<SidebarSolidContainerProps> = ({
  handleID,
  explorerPath,
  getInvocations,
  showingSubsolids,
  onEnterCompositeSolid,
  onClickSolid,
  repoAddress,
}) => {
  const pipelineSelector = usePipelineSelector(repoAddress || null, explorerPath.pipelineName);
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
              repoAddress={repoAddress}
            />
          </>
        );
      }}
    </Loading>
  );
};

const SIDEBAR_TABBED_CONTAINER_SOLID_QUERY = gql`
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
  ${SIDEBAR_SOLID_INVOCATION_FRAGMENT}
  ${SIDEBAR_SOLID_DEFINITION_FRAGMENT}
`;
