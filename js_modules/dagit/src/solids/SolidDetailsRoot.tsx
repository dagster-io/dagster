import gql from 'graphql-tag';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {RouteComponentProps} from 'react-router';
import styled from 'styled-components/macro';

import {DagsterRepositoryContext, useRepositorySelector} from '../DagsterRepositoryContext';
import Loading from '../Loading';
import {SidebarSolidDefinition} from '../SidebarSolidDefinition';
import {SidebarSolidInvocationInfo} from '../SidebarSolidHelpers';

import {SolidCard} from './SolidCard';
import {UsedSolidDetailsQuery} from './types/UsedSolidDetailsQuery';

export const SolidDetailsRoot: React.FunctionComponent<RouteComponentProps<{
  name: string;
}>> = (props) => (
  <SolidDetailScrollContainer>
    <UsedSolidDetails
      name={props.match.params.name}
      onClickInvocation={({pipelineName, handleID}) =>
        props.history.push(`/pipeline/${pipelineName}/${handleID.split('.').join('/')}`)
      }
    />
  </SolidDetailScrollContainer>
);

export const UsedSolidDetails: React.FunctionComponent<{
  name: string;
  onClickInvocation: (arg: SidebarSolidInvocationInfo) => void;
}> = ({name, onClickInvocation}) => {
  const {repositoryLocation, repository} = React.useContext(DagsterRepositoryContext);
  const repositorySelector = useRepositorySelector();
  const queryResult = useQuery<UsedSolidDetailsQuery>(USED_SOLID_DETAILS_QUERY, {
    skip: !repository || !repositoryLocation,
    variables: {
      name,
      repositorySelector,
    },
  });

  return (
    <Loading queryResult={queryResult}>
      {({repositoryOrError}) => {
        if (!(repositoryOrError?.__typename === 'Repository' && repositoryOrError.usedSolid)) {
          return null;
        }
        const usedSolid = repositoryOrError.usedSolid;
        return (
          <>
            <SolidCard definition={usedSolid.definition} />
            <SidebarSolidDefinition
              definition={usedSolid.definition}
              showingSubsolids={false}
              onClickInvocation={onClickInvocation}
              getInvocations={() => {
                return usedSolid.invocations.map((i) => ({
                  handleID: i.solidHandle.handleID,
                  pipelineName: i.pipeline.name,
                }));
              }}
            />
          </>
        );
      }}
    </Loading>
  );
};

export const USED_SOLID_DETAILS_QUERY = gql`
  query UsedSolidDetailsQuery($name: String!, $repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        usedSolid(name: $name) {
          __typename
          definition {
            ...SolidCardSolidDefinitionFragment
            ...SidebarSolidDefinitionFragment
          }
          invocations {
            __typename
            pipeline {
              name
            }
            solidHandle {
              handleID
            }
          }
        }
      }
    }
  }

  ${SolidCard.fragments.SolidCardSolidDefinitionFragment}
  ${SidebarSolidDefinition.fragments.SidebarSolidDefinitionFragment}
`;

export const SolidDetailScrollContainer = styled.div`
  overflow: scroll;
  flex: 1;
`;
