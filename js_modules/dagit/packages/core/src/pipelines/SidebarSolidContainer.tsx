import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {SolidNameOrPath} from '../solids/SolidNameOrPath';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {LoadingSpinner} from '../ui/Loading';
import {NonIdealState} from '../ui/NonIdealState';
import {RepoAddress} from '../workspace/types';

import {ExplorerPath} from './PipelinePathUtils';
import {SidebarSolidDefinition, SIDEBAR_SOLID_DEFINITION_FRAGMENT} from './SidebarSolidDefinition';
import {SidebarSolidInvocation, SIDEBAR_SOLID_INVOCATION_FRAGMENT} from './SidebarSolidInvocation';
import {
  SidebarGraphSolidQuery,
  SidebarGraphSolidQueryVariables,
} from './types/SidebarGraphSolidQuery';
import {
  SidebarPipelineSolidQuery,
  SidebarPipelineSolidQueryVariables,
} from './types/SidebarPipelineSolidQuery';
import {SidebarSolidContainerFragment} from './types/SidebarSolidContainerFragment';

interface SidebarSolidContainerProps {
  handleID: string;
  explorerPath: ExplorerPath;
  showingSubsolids: boolean;
  parentSolidHandleID?: string;
  getInvocations?: (definitionName: string) => {handleID: string}[];
  onEnterCompositeSolid: (arg: SolidNameOrPath) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
  repoAddress?: RepoAddress;
  isGraph: boolean;
}

const useSidebarSolidQuery = (
  name: string,
  handleID: string,
  isGraph: boolean,
  repoAddress?: RepoAddress,
) => {
  const pipelineResult = useQuery<SidebarPipelineSolidQuery, SidebarPipelineSolidQueryVariables>(
    SIDEBAR_PIPELINE_SOLID_QUERY,
    {
      variables: {
        selector: {
          repositoryName: repoAddress?.name || '',
          repositoryLocationName: repoAddress?.location || '',
          pipelineName: name,
        },
        handleID: handleID,
      },
      fetchPolicy: 'cache-and-network',
      skip: isGraph,
    },
  );

  const graphResult = useQuery<SidebarGraphSolidQuery, SidebarGraphSolidQueryVariables>(
    SIDEBAR_GRAPH_SOLID_QUERY,
    {
      variables: {
        selector: {
          repositoryName: repoAddress?.name || '',
          repositoryLocationName: repoAddress?.location || '',
          graphName: name,
        },
        handleID: handleID,
      },
      fetchPolicy: 'cache-and-network',
      skip: !isGraph,
    },
  );

  if (isGraph) {
    const {error, data, loading} = graphResult;
    const solidContainer: SidebarSolidContainerFragment | undefined =
      data?.graphOrError.__typename === 'Graph' ? data.graphOrError : undefined;
    return {
      error,
      solidContainer,
      isLoading: !!loading,
    };
  }

  const {error, data, loading} = pipelineResult;
  const solidContainer: SidebarSolidContainerFragment | undefined =
    data?.pipelineOrError.__typename === 'Pipeline' ? data.pipelineOrError : undefined;
  return {
    error,
    solidContainer,
    isLoading: !!loading,
  };
};

export const SidebarSolidContainer: React.FC<SidebarSolidContainerProps> = ({
  handleID,
  explorerPath,
  getInvocations,
  showingSubsolids,
  onEnterCompositeSolid,
  onClickSolid,
  repoAddress,
  isGraph,
}) => {
  // const pipelineSelector = buildPipelineSelector(repoAddress || null, explorerPath.pipelineName);
  const {error, solidContainer, isLoading} = useSidebarSolidQuery(
    explorerPath.pipelineName,
    handleID,
    isGraph,
    repoAddress,
  );
  if (error) {
    console.error(error);
    return (
      <Box padding={64} flex={{justifyContent: 'center'}}>
        <NonIdealState icon="error" title="GraphQL Error - see console for details" />
      </Box>
    );
  }

  if (isLoading) {
    return <LoadingSpinner purpose="section" />;
  }

  if (!solidContainer) {
    console.error('Could not load solids');
    return (
      <Box padding={{vertical: 16, horizontal: 24}} style={{color: ColorsWIP.Gray500}}>
        Could not load solids.
      </Box>
    );
  }

  return (
    <>
      <SidebarSolidInvocation
        key={`${handleID}-inv`}
        solid={solidContainer!.solidHandle!.solid}
        onEnterCompositeSolid={
          solidContainer!.solidHandle!.solid.definition.__typename === 'CompositeSolidDefinition'
            ? onEnterCompositeSolid
            : undefined
        }
      />
      <SidebarSolidDefinition
        key={`${handleID}-def`}
        showingSubsolids={showingSubsolids}
        definition={solidContainer!.solidHandle!.solid.definition}
        getInvocations={getInvocations}
        onClickInvocation={({handleID}) => onClickSolid({path: handleID.split('.')})}
        repoAddress={repoAddress}
      />
    </>
  );
};

const SIDEBAR_SOLID_CONTAINER_FRAGMENT = gql`
  fragment SidebarSolidContainerFragment on SolidContainer {
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
  ${SIDEBAR_SOLID_INVOCATION_FRAGMENT}
  ${SIDEBAR_SOLID_DEFINITION_FRAGMENT}
`;

const SIDEBAR_PIPELINE_SOLID_QUERY = gql`
  query SidebarPipelineSolidQuery($selector: PipelineSelector!, $handleID: String!) {
    pipelineOrError(params: $selector) {
      __typename
      ... on Pipeline {
        id
        ...SidebarSolidContainerFragment
      }
    }
  }
  ${SIDEBAR_SOLID_CONTAINER_FRAGMENT}
`;

const SIDEBAR_GRAPH_SOLID_QUERY = gql`
  query SidebarGraphSolidQuery($selector: GraphSelector!, $handleID: String!) {
    graphOrError(selector: $selector) {
      __typename
      ... on Graph {
        id
        ...SidebarSolidContainerFragment
      }
    }
  }
  ${SIDEBAR_SOLID_CONTAINER_FRAGMENT}
`;
